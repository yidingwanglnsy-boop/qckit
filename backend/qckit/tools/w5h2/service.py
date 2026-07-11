"""5W2H 分析法（表格版）—— 多根因批量分析。

每行一条根因，7 列：What / Why(必填) / Where / When / Who / How / How Much
空缺字段由 LLM 基于该行 Why 联想补全，用户已填字段绝不覆盖。
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register


FIELDS = ["what", "where", "when", "who", "how", "how_much"]
FIELD_LABEL = {
    "what": "What", "why": "Why", "where": "Where", "when": "When",
    "who": "Who", "how": "How", "how_much": "How Much",
}


class W5H2Row(BaseModel):
    why: str = Field(..., description="根本原因（必填）")
    what: str = ""
    where: str = ""
    when: str = ""
    who: str = ""
    how: str = ""
    how_much: str = ""

    @model_validator(mode="after")
    def _clean(self):
        for f in FIELDS + ["why"]:
            setattr(self, f, (getattr(self, f) or "").strip())
        if len(self.why) < 2:
            raise ValueError("Why (根本原因) 至少 2 个字符")
        return self


class W5H2Request(BaseModel):
    topic: str = Field(..., description="分析主题")
    rows: list[W5H2Row] = Field(..., min_length=1, max_length=30)
    context: str | None = None
    use_llm: bool = True


class W5H2RowOut(BaseModel):
    why: str
    what: str
    where: str
    when: str
    who: str
    how: str
    how_much: str
    inferred: list[str] = []


class W5H2Response(BaseModel):
    topic: str
    rows: list[W5H2RowOut]
    reasoning: str = ""


SYSTEM = """你是精通 QC 与项目改善的顾问，熟悉 5W2H 分析法。用户会给出主题和一张表格，
每行是一条根因（Why）+ 6 列可选字段。你只需针对**空缺字段**基于该行 Why 联想推理，
给出具体、可执行、贴合制造业/QC 场景的内容。已填字段绝对不要改。

严格返回 JSON：
{
  "rows": [
    {"what":"...","where":"...","when":"...","who":"...","how":"...","how_much":"..."},
    ...
  ],
  "reasoning": "…整体推理逻辑, 150 字内"
}

rows 顺序必须与输入一致；每一行只输出**空缺**字段的 key（已填字段的 key 省略）。
字段值要**具体**（如"2 周内完成"、"车间主任+QC 组长"、"减少不良 30%"），不要说"待定/需讨论"。"""


def analyze(req: W5H2Request) -> W5H2Response:
    rows_out: list[W5H2RowOut] = []
    reasoning = ""

    any_missing = any(not getattr(r, f) for r in req.rows for f in FIELDS)

    ai_rows: list[dict] = [{} for _ in req.rows]
    if req.use_llm and any_missing:
        lines = []
        for i, r in enumerate(req.rows, 1):
            lines.append(f"\n第 {i} 行:")
            lines.append(f"  Why: {r.why}")
            for f in FIELDS:
                v = getattr(r, f)
                if v:
                    lines.append(f"  {FIELD_LABEL[f]}: {v}")
                else:
                    lines.append(f"  {FIELD_LABEL[f]}: (待补全)")
        user = f"主题: {req.topic}\n背景: {req.context or '（无）'}\n" + "\n".join(lines)
        try:
            data = chat_json(SYSTEM, user)
            for i, rr in enumerate(data.get("rows", [])):
                if i < len(ai_rows) and isinstance(rr, dict):
                    ai_rows[i] = rr
            reasoning = str(data.get("reasoning", "")).strip()
        except Exception as e:
            reasoning = f"（LLM 推理失败：{e}）"

    for req_row, ai in zip(req.rows, ai_rows):
        inferred: list[str] = []
        merged: dict[str, str] = {"why": req_row.why}
        for f in FIELDS:
            given = getattr(req_row, f)
            if given:
                merged[f] = given
            else:
                ai_val = str(ai.get(f, "")).strip() if ai else ""
                merged[f] = ai_val
                if ai_val:
                    inferred.append(f)
        rows_out.append(W5H2RowOut(**merged, inferred=inferred))

    return W5H2Response(topic=req.topic, rows=rows_out, reasoning=reasoning)


register(ToolMeta(
    key="w5h2",
    name="5W2H 分析",
    category="通用工具",
    description="批量根因 5W2H 表格，空缺字段 LLM 联想补全，支持 Excel 粘贴。",
    icon="Grid",
))
