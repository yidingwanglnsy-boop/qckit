"""5W2H 分析法 —— 结构化对策展开。

Why (根因) 为必填字段。其他 6 项 (What/Where/When/Who/How/HowMuch)
用户已填的原样保留，未填的由 LLM 基于 Why 联想推理补全。
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register


FIELDS = ["what", "where", "when", "who", "how", "how_much"]
FIELD_LABELS = {
    "what":     ("What",     "问题/现象是什么"),
    "why":      ("Why",      "根本原因（必填）"),
    "where":    ("Where",    "发生地点/环节"),
    "when":     ("When",     "时间节点/期限"),
    "who":      ("Who",      "责任人/参与者"),
    "how":      ("How",      "对策方案/措施"),
    "how_much": ("How Much", "成本/目标/工时"),
}


class W5H2Request(BaseModel):
    topic: str = Field(..., description="分析主题")
    why: str = Field(..., min_length=2, description="根本原因（必填）")
    what: str = ""
    where: str = ""
    when: str = ""
    who: str = ""
    how: str = ""
    how_much: str = ""
    context: str | None = None
    use_llm: bool = Field(True, description="缺失字段是否用 LLM 联想补全")

    @model_validator(mode="after")
    def _clean(self):
        for f in FIELDS:
            setattr(self, f, (getattr(self, f) or "").strip())
        return self


class W5H2Response(BaseModel):
    topic: str
    what: str
    why: str
    where: str
    when: str
    who: str
    how: str
    how_much: str
    inferred: list[str] = []   # LLM 推理补全过的字段名
    reasoning: str = ""        # LLM 简述推理逻辑（可选）


SYSTEM = """你是精通 QC 与项目改善的顾问，熟悉 5W2H 分析法。用户会给出主题、根本原因（Why），
以及可能已填部分字段。你需要针对**未填写**的字段基于 Why 进行合理联想推理，给出具体、
可执行、贴合制造业/QC 场景的内容。已填字段不要改动。

输出严格 JSON，仅包含需要补全的字段与简短推理：
{
  "what": "...",     // 未填时给出问题现象描述
  "where": "...",    // 未填时推理发生地点/工序
  "when": "...",     // 未填时给出时间节点建议 (如 "本月内 / 2 周内")
  "who": "...",      // 未填时建议责任岗位
  "how": "...",      // 未填时给出 1-3 条具体对策 (用 / 分隔)
  "how_much": "...", // 未填时给出目标或成本估计
  "reasoning": "..." // 一段话简述你的推理逻辑 (100 字内)
}

只输出**未填**字段的 key。已填字段的 key 直接省略不写。字段值要**具体**（不要说"待定/需讨论"）。"""


def analyze(req: W5H2Request) -> W5H2Response:
    given = {f: getattr(req, f) for f in FIELDS}
    missing = [f for f, v in given.items() if not v]

    inferred: dict[str, str] = {}
    reasoning = ""
    if req.use_llm and missing:
        parts = [f"主题: {req.topic}", f"Why (根因): {req.why}"]
        if req.context:
            parts.append(f"背景: {req.context}")
        parts.append("\n已填字段:")
        for f in FIELDS:
            if given[f]:
                lbl, _ = FIELD_LABELS[f]
                parts.append(f"  {lbl}: {given[f]}")
        parts.append(f"\n待补全字段: {', '.join(FIELD_LABELS[f][0] for f in missing)}")
        parts.append("\n按 system schema 只输出待补全字段的 JSON。")
        try:
            data = chat_json(SYSTEM, "\n".join(parts))
            for f in missing:
                v = str(data.get(f, "")).strip()
                if v:
                    inferred[f] = v
            reasoning = str(data.get("reasoning", "")).strip()
        except Exception as e:
            reasoning = f"（LLM 推理失败：{e}）"

    return W5H2Response(
        topic=req.topic,
        why=req.why,
        what=given["what"] or inferred.get("what", ""),
        where=given["where"] or inferred.get("where", ""),
        when=given["when"] or inferred.get("when", ""),
        who=given["who"] or inferred.get("who", ""),
        how=given["how"] or inferred.get("how", ""),
        how_much=given["how_much"] or inferred.get("how_much", ""),
        inferred=list(inferred.keys()),
        reasoning=reasoning,
    )


register(ToolMeta(
    key="w5h2",
    name="5W2H 分析",
    category="通用工具",
    description="根因驱动的对策展开：Why 必填，其他字段 LLM 联想补全。",
    icon="Grid",
))
