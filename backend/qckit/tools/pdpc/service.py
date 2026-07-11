"""PDPC 法 (过程决策程序图) —— 前瞻性列出每步的风险与对策。"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register


class PDPCRequest(BaseModel):
    topic: str = Field(..., description="目标事件")
    steps: list[str] | None = Field(None, description="主流程步骤 (可选, LLM 会补)")
    risk_dims: list[str] | None = Field(None, description="关注风险维度 (供应/技术/质量/进度)")
    context: str | None = None


class PDPCNode(BaseModel):
    id: str
    label: str
    kind: str            # step / risk / countermeasure / success / fail
    parent: str | None = None
    probability: str = ""   # H/M/L
    impact: str = ""        # H/M/L
    priority: str = ""      # P1/P2/P3
    trigger: str = ""       # 预警指标/触发条件
    owner: str = ""


class PDPCResponse(BaseModel):
    topic: str
    nodes: list[PDPCNode]
    top_risks: list[dict] = []
    summary: str = ""
    recommendations: list[str] = []


SYSTEM_PROMPT = """你是 QC 新七大手法「PDPC 过程决策程序图」专家。
根据目标事件, 展开:
1. 主流程 (step): 3-6 步
2. 每步下挂 2-3 个可能风险 (risk), 标 probability(H/M/L) × impact(H/M/L)
3. 每风险下挂 1-2 个对策 (countermeasure), 含 trigger(触发条件/预警指标) 和 owner(角色)
4. 每对策指向 success 或 fail 分支
5. 找出 Top 5 高危路径 (P × I 最高)

严格 JSON:
{
  "nodes":[
    {"id":"S1","kind":"step","label":"第一步","parent":null},
    {"id":"R1_1","kind":"risk","label":"风险描述","parent":"S1",
      "probability":"H","impact":"M"},
    {"id":"C1_1_1","kind":"countermeasure","label":"对策","parent":"R1_1",
      "trigger":"预警条件","owner":"角色"},
    {"id":"OK1_1_1","kind":"success","label":"进入下一步","parent":"C1_1_1"}
  ],
  "top_risks":[{"risk":"...","score":9,"path":"S1→R1_1","action":"..."}],
  "summary":"整图解读",
  "recommendations":["Top 3 需立即准备预案"]
}
priority 由后端根据 H/M/L 自动算 (HH=P1, HM/MH=P2, 其余=P3), 你不用填。
"""


def _prio(p: str, i: str) -> str:
    p, i = p.upper(), i.upper()
    if p == "H" and i == "H":
        return "P1"
    if {p, i} == {"H", "M"} or (p == "H" and i == "M") or (p == "M" and i == "H"):
        return "P2"
    return "P3"


def analyze(req: PDPCRequest) -> PDPCResponse:
    ctx_bits = []
    if req.context:
        ctx_bits.append(f"背景: {req.context}")
    if req.steps:
        ctx_bits.append(f"主流程建议: {', '.join(req.steps)}")
    if req.risk_dims:
        ctx_bits.append(f"关注风险维度: {', '.join(req.risk_dims)}")
    user = f"目标事件: {req.topic}\n" + "\n".join(ctx_bits)
    data = chat_json(SYSTEM_PROMPT, user)

    nodes: list[PDPCNode] = []
    for n in data.get("nodes", []):
        kind = n.get("kind", "step")
        prob = str(n.get("probability", "") or "").upper()
        imp = str(n.get("impact", "") or "").upper()
        nodes.append(PDPCNode(
            id=n.get("id", ""),
            label=n.get("label", ""),
            kind=kind if kind in ("step", "risk", "countermeasure", "success", "fail") else "step",
            parent=n.get("parent"),
            probability=prob if prob in ("H", "M", "L") else "",
            impact=imp if imp in ("H", "M", "L") else "",
            priority=_prio(prob, imp) if kind == "risk" else "",
            trigger=n.get("trigger", ""),
            owner=n.get("owner", ""),
        ))

    return PDPCResponse(
        topic=req.topic,
        nodes=nodes,
        top_risks=list(data.get("top_risks", []))[:8],
        summary=data.get("summary", ""),
        recommendations=list(data.get("recommendations", []))[:8],
    )


register(ToolMeta(
    key="pdpc",
    name="PDPC 过程决策程序图",
    category="新QC七大手法",
    description="前瞻性列出流程各步的风险 × 对策, 预防性思维必备。",
    icon="Compass",
))
