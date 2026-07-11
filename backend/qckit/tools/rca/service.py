"""根因确认（Root Cause Analysis / 要因确认）—— QCC 常用手法。

一个"症结"下可挂 N 条"末端原因"（1:N）；每条末端原因需要给出
确认内容 / 确认方法 / 确认结果 / 责任人 / 完成时间 / 是否要因。

前端以扁平表格提交，症结重复即表达 1:N。后端只对空缺字段做 LLM 联想补全，
用户已填字段绝不覆盖。
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register

FIELDS = ["content", "method", "result", "owner", "due", "is_key"]
FIELD_LABEL = {
    "symptom":  "症结",
    "cause":    "末端原因",
    "content":  "确认内容",
    "method":   "确认方法",
    "result":   "确认结果",
    "owner":    "责任人",
    "due":      "完成时间",
    "is_key":   "是否要因",
}
# LLM 只补下面 4 列；owner/due 是行政字段，不联想
AI_FIELDS = ["content", "method", "result", "is_key"]


class RcaRow(BaseModel):
    symptom: str = Field(..., description="症结（必填）")
    cause:   str = Field(..., description="末端原因（必填）")
    content: str = ""
    method:  str = ""
    result:  str = ""
    owner:   str = ""
    due:     str = ""
    is_key:  str = ""  # "是"/"否"/"待验证" 等自由文本

    @model_validator(mode="after")
    def _clean(self):
        for f in ["symptom", "cause"] + FIELDS:
            setattr(self, f, (getattr(self, f) or "").strip())
        if len(self.symptom) < 2:
            raise ValueError("症结 至少 2 个字符")
        if len(self.cause) < 2:
            raise ValueError("末端原因 至少 2 个字符")
        return self


class RcaRequest(BaseModel):
    topic:   str = Field(..., description="分析主题")
    rows:    list[RcaRow] = Field(..., min_length=1, max_length=60)
    context: str | None = None
    use_llm: bool = True


class RcaRowOut(BaseModel):
    symptom: str
    cause:   str
    content: str = ""
    method:  str = ""
    result:  str = ""
    owner:   str = ""
    due:     str = ""
    is_key:  str = ""
    inferred: list[str] = []


class RcaResponse(BaseModel):
    topic:     str
    rows:      list[RcaRowOut]
    reasoning: str = ""


SYSTEM = """你是精通 QCC / 六西格玛的资深质量顾问，熟悉"要因确认"手法。
用户给出主题与一张表格：每行是一条 (症结, 末端原因) 组合，同一症结可有多条末端原因。
你只针对**空缺字段**做联想补全，已填字段绝对不要改。可联想字段：
  - content 确认内容：具体要验证什么现象/数据/条件
  - method  确认方法：现场测量 / 数据分析 / 试验对比 / 访谈 / 抽样检验 等，尽量给出具体做法
  - result  确认结果：一句话陈述验证后的结论方向（可含"符合/不符合规范"等）
  - is_key  是否要因：仅返回 "是" / "否" / "待验证" 之一

严格返回 JSON:
{
  "rows": [
    {"content":"...","method":"...","result":"...","is_key":"是"},
    ...
  ],
  "reasoning": "整体推理逻辑, 150 字内"
}

rows 顺序必须与输入一致；每行只输出**空缺**字段的 key（已填字段的 key 省略）。
内容要具体、贴合制造业/QC 场景，不要"待定/需讨论"这种废话。"""


def analyze(req: RcaRequest) -> RcaResponse:
    reasoning = ""
    ai_rows: list[dict] = [{} for _ in req.rows]

    any_missing = any(not getattr(r, f) for r in req.rows for f in AI_FIELDS)
    if req.use_llm and any_missing:
        lines = []
        for i, r in enumerate(req.rows, 1):
            lines.append(f"\n第 {i} 行:")
            lines.append(f"  症结: {r.symptom}")
            lines.append(f"  末端原因: {r.cause}")
            for f in AI_FIELDS:
                v = getattr(r, f)
                lines.append(f"  {FIELD_LABEL[f]}: {v if v else '(待补全)'}")
        user = f"主题: {req.topic}\n背景: {req.context or '（无）'}\n" + "\n".join(lines)
        try:
            data = chat_json(SYSTEM, user)
            for i, rr in enumerate(data.get("rows", [])):
                if i < len(ai_rows) and isinstance(rr, dict):
                    ai_rows[i] = rr
            reasoning = str(data.get("reasoning", "")).strip()
        except Exception as e:
            reasoning = f"（LLM 推理失败：{e}）"

    rows_out: list[RcaRowOut] = []
    for req_row, ai in zip(req.rows, ai_rows):
        inferred: list[str] = []
        merged: dict[str, str] = {
            "symptom": req_row.symptom,
            "cause":   req_row.cause,
            "owner":   req_row.owner,
            "due":     req_row.due,
        }
        for f in AI_FIELDS:
            given = getattr(req_row, f)
            if given:
                merged[f] = given
            else:
                ai_val = str(ai.get(f, "")).strip() if ai else ""
                merged[f] = ai_val
                if ai_val:
                    inferred.append(f)
        rows_out.append(RcaRowOut(**merged, inferred=inferred))

    return RcaResponse(topic=req.topic, rows=rows_out, reasoning=reasoning)


register(ToolMeta(
    key="rca",
    name="根因确认",
    category="通用工具",
    description="要因确认表：症结→末端原因（1:N），LLM 联想补全确认内容/方法/结果/是否要因，支持 Excel 粘贴。",
    icon="Search",
))
