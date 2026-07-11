"""鱼骨图（Ishikawa / Fishbone）—— 4M 分类 + 层级末端原因。

输入: 主题、背景、可选的初始末端原因列表、每类目标数、层数(1/2/3)
LLM 做两件事:
  1. 分类: 把已有末端原因归入 人/机/料/法; 数量不足则联想补齐到 target_per_category
  2. 层级: 层数=2 时在每个大类下再产出子类, 层数=3 时子类下再产出末端

输出: 4M 树 {category: {name, children: [{name, children:[...]}]}}
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register

CATEGORIES = ["人", "机", "料", "法"]
CATEGORY_EN = {"人": "Man", "机": "Machine", "料": "Material", "法": "Method"}


class FishboneNode(BaseModel):
    name: str
    inferred: bool = False
    children: list["FishboneNode"] = []


FishboneNode.model_rebuild()


class FishboneRequest(BaseModel):
    topic:   str = Field(..., description="鱼头 - 问题/结果")
    context: str = ""
    causes:  list[str] = Field(default_factory=list, description="初始末端原因，可空")
    target_per_category: int = Field(4, ge=1, le=12, description="每类目标条数")
    layers:  Literal[1, 2, 3] = 2


class FishboneCategory(BaseModel):
    category: str  # 人/机/料/法
    name:     str  # 中英组合，如 "人 (Man)"
    children: list[FishboneNode] = []


class FishboneResponse(BaseModel):
    topic:      str
    context:    str = ""
    categories: list[FishboneCategory]
    reasoning:  str = ""


SYSTEM_TEMPLATE = """你是精通 QC 鱼骨图（4M）分析的顾问，熟悉制造业 QCC 场景。
用户给出一个问题（鱼头）和可选的末端原因清单。你需要：
1. 把每条已有末端原因严格归入 人/机/料/法 之一（不允许其它类别）
2. 如果某个类别下的末端数量少于 target={target}, 联想补齐到 target 条
3. 层数 layers={layers}:
   - 1: 直接给出末端原因数组 children=[{{"name":"..."}}, ...]
   - 2: 在每个大类下先分 2-4 个子类, 再挂末端。结构:
        children=[{{"name":"子类A","children":[{{"name":"末端1"}},{{"name":"末端2"}}]}}, ...]
   - 3: 子类下再细分, 三层树

严格返回 JSON:
{{
  "categories": {{
    "人": [ ...children... ],
    "机": [ ...children... ],
    "料": [ ...children... ],
    "法": [ ...children... ]
  }},
  "inferred": ["新增的末端原因文本1", "新增的末端原因文本2", ...],
  "reasoning": "整体推理逻辑, 150 字内"
}}

要点:
- children 元素统一是 {{"name":"...", "children":[...]}}（第 3 层无 children）
- "inferred" 列出你补齐/新增的末端原因文本，用于前端标识
- 内容要具体、贴合场景（如 "焊工技能等级 3 级以下占 40%"）不要"待定"
- 每类至少 1 条；已有末端原因原样保留，不要改文字"""


def _walk_mark_inferred(nodes: list[dict], inferred_set: set[str]) -> list[FishboneNode]:
    out: list[FishboneNode] = []
    for n in nodes or []:
        if not isinstance(n, dict):
            continue
        name = str(n.get("name", "")).strip()
        if not name:
            continue
        children = _walk_mark_inferred(n.get("children") or [], inferred_set)
        out.append(FishboneNode(name=name, inferred=name in inferred_set, children=children))
    return out


def analyze(req: FishboneRequest) -> FishboneResponse:
    lines = [f"主题: {req.topic}", f"背景: {req.context or '（无）'}"]
    if req.causes:
        lines.append("已有末端原因:")
        for c in req.causes:
            lines.append(f"  - {c}")
    else:
        lines.append("（无已有末端原因，请全部联想生成）")
    user = "\n".join(lines)

    system = SYSTEM_TEMPLATE.format(target=req.target_per_category, layers=req.layers)

    try:
        data = chat_json(system, user)
    except Exception as e:
        # LLM 失败时，把已有 causes 平均分到 4 类，保证至少能画图
        buckets: dict[str, list[str]] = {c: [] for c in CATEGORIES}
        for i, c in enumerate(req.causes):
            buckets[CATEGORIES[i % 4]].append(c)
        return FishboneResponse(
            topic=req.topic, context=req.context,
            categories=[
                FishboneCategory(
                    category=cat, name=f"{cat} ({CATEGORY_EN[cat]})",
                    children=[FishboneNode(name=n) for n in buckets[cat]],
                ) for cat in CATEGORIES
            ],
            reasoning=f"（LLM 失败: {e}；已按顺序平均分配已有原因）",
        )

    inferred_set = {str(x).strip() for x in (data.get("inferred") or []) if str(x).strip()}
    cats_raw = data.get("categories") or {}

    categories: list[FishboneCategory] = []
    for cat in CATEGORIES:
        children_raw = cats_raw.get(cat) or []
        categories.append(FishboneCategory(
            category=cat, name=f"{cat} ({CATEGORY_EN[cat]})",
            children=_walk_mark_inferred(children_raw, inferred_set),
        ))

    return FishboneResponse(
        topic=req.topic, context=req.context,
        categories=categories,
        reasoning=str(data.get("reasoning", "")).strip(),
    )


register(ToolMeta(
    key="fishbone",
    name="鱼骨图（4M）",
    category="QC七大手法",
    description="自动 4M 分类（人/机/料/法）+ 多层级末端原因，末端数量不足时 LLM 联想补齐。",
    icon="Share",
))
