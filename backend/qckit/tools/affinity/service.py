"""亲和图（KJ 法 / Affinity Diagram）。

输入：一堆零散的观点、意见、问题条目（头脑风暴产物）
输出：LLM 自动聚类 → 每组一个主题名 + 组间关系
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register


class AffinityRequest(BaseModel):
    topic: str = Field(..., description="主题/情境")
    items: list[str] = Field(..., min_length=3, description="零散条目")
    target_groups: int | None = Field(None, description="期望分组数，可选")
    context: str | None = None


class GroupOut(BaseModel):
    id: str
    name: str          # 主题名（4-10 字）
    summary: str       # 一句话描述
    items: list[str]   # 归入本组的原始条目
    priority: int = 2  # 1-3，1=最高


class GroupLinkOut(BaseModel):
    source: str
    target: str
    relation: str = ""   # 2-6 字关系词


class AffinityResponse(BaseModel):
    topic: str
    groups: list[GroupOut]
    links: list[GroupLinkOut]
    insights: str
    recommendations: list[str] = []


SYSTEM = """你是精通 KJ 法（亲和图）的质量顾问。KJ 法把大量零散的原始观点自下而上聚合成有意义的主题簇。

必须严格返回 JSON：
{
  "groups": [
    {"id": "g1", "name": "主题名（4-10 字）", "summary": "一句话（30 字内）",
     "items": ["原始条目一字不改", "..."], "priority": 1|2|3}
  ],
  "links": [{"source":"g1","target":"g2","relation":"2-6 字关系词"}],
  "insights": "整体洞察（150 字内）",
  "recommendations": ["行动建议1", "..."]
}

规则：
1. items 内容必须是**原样引用**输入条目（不改写）。所有条目必须归入且仅归入某一组。
2. 组数一般 3-7，除非用户指定 target_groups。
3. name 是抽象后的主题（如「培训机制不健全」），不是条目复述。
4. priority: 1=最高优先级（人数多/影响大/根本），3=次要。
5. links 只在组间有明显相关/因果时才连。
6. relation 是极简词组：导致、加剧、伴随、共因、诱发、影响等。
"""


def analyze(req: AffinityRequest) -> AffinityResponse:
    items_lines = "\n".join(f"- {s}" for s in req.items)
    hint = f"期望分组数：{req.target_groups}" if req.target_groups else "自主决定分组数"
    user = f"""主题：{req.topic}
背景：{req.context or "（无）"}
{hint}

原始条目：
{items_lines}

按 system schema 返回 JSON。"""

    data = chat_json(SYSTEM, user)

    # 校验 + 兜底
    all_items = set(req.items)
    groups: list[GroupOut] = []
    seen: set[str] = set()
    for g in data.get("groups", []):
        items = [it for it in g.get("items", []) if it in all_items and it not in seen]
        seen.update(items)
        groups.append(GroupOut(
            id=g.get("id") or f"g{len(groups)+1}",
            name=g.get("name", "未命名组"),
            summary=g.get("summary", ""),
            items=items,
            priority=_clamp(int(g.get("priority", 2) or 2), 1, 3),
        ))

    # 未归类条目 → 追加"其他"组
    orphans = [it for it in req.items if it not in seen]
    if orphans:
        groups.append(GroupOut(id=f"g{len(groups)+1}", name="其他",
                               summary="未能归入其他主题的条目", items=orphans, priority=3))

    valid = {g.id for g in groups}
    links = [GroupLinkOut(source=l["source"], target=l["target"], relation=l.get("relation", ""))
             for l in data.get("links", [])
             if l.get("source") in valid and l.get("target") in valid and l["source"] != l["target"]]

    return AffinityResponse(
        topic=req.topic, groups=groups, links=links,
        insights=data.get("insights", ""),
        recommendations=list(data.get("recommendations", []))[:8],
    )


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


register(ToolMeta(
    key="affinity",
    name="亲和图（KJ 法）",
    category="新QC七大手法",
    description="把大量零散观点自动聚类成有意义的主题簇。",
    icon="Collection",
))
