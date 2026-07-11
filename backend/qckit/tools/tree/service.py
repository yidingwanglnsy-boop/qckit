"""系统图（Tree Diagram）——把目标层层拆到可执行行动。

LLM 一次性生成 3 层拆解树, 叶节点带 SMART 化 + PICK 评分。
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register


class TreeRequest(BaseModel):
    topic: str = Field(..., description="顶层目的（1 句话）")
    context: str | None = Field(None, description="背景/约束")
    layers: int = Field(3, ge=2, le=4, description="目标层数")
    hints: list[str] | None = Field(None, description="已有想法，可选")


class TreeNode(BaseModel):
    id: str
    label: str
    level: int         # 0=root, 1..N
    parent: str | None = None
    smart: str = ""            # 叶节点 SMART 化描述
    payoff: int = 0            # 收益 1-5
    feasibility: int = 0       # 可行性 1-5
    priority: str = ""         # P1/P2/P3
    is_leaf: bool = False


class TreeResponse(BaseModel):
    topic: str
    nodes: list[TreeNode]
    mece_check: list[str] = []      # 各支的 MECE 提示
    summary: str = ""
    recommendations: list[str] = []


SYSTEM_PROMPT = """你是 QC 新七大手法「系统图法（Tree Diagram）」专家。
把一个大目标层层拆解为可执行动作。规则：
1. 树根 = 用户输入的 topic；下一层是主要手段类别（3-5 个，MECE，覆盖人机料法环等维度）。
2. 逐层继续展开，共 {layers} 层。最后一层是「叶节点」= 可执行动作。
3. 叶节点必须 SMART 化：具体、可量化、有时限（如："每周三 15:00 培训焊工电流参数, Q4 达 100% 覆盖"）。
4. 叶节点给 payoff(收益 1-5) × feasibility(可行性 1-5)。
5. 每个主类别（第 1 层）给一句 MECE 反思提示（如："此支已覆盖人+法, 但缺'机'维度, 建议补充设备巡检"）。

严格返回 JSON:
{
  "nodes": [
    {"id":"root","label":"顶层目标","level":0,"parent":null,"is_leaf":false},
    {"id":"L1_1","label":"主类别1","level":1,"parent":"root","is_leaf":false},
    {"id":"L2_1_1","label":"子手段","level":2,"parent":"L1_1","is_leaf":false},
    {"id":"L3_1_1_1","label":"叶动作","level":3,"parent":"L2_1_1","is_leaf":true,
     "smart":"SMART 化描述", "payoff":4, "feasibility":3}
  ],
  "mece_check":["主类别1: 提示", "主类别2: 提示"],
  "summary":"整树解读 100 字内",
  "recommendations":["优先做...", "..."]
}
id 命名严格用 L<层>_<父序>_<自序> 保证唯一。
"""


def analyze(req: TreeRequest) -> TreeResponse:
    ctx = f"\n背景: {req.context}" if req.context else ""
    hints = f"\n已有想法: {', '.join(req.hints)}" if req.hints else ""
    user = f"目标: {req.topic}{ctx}{hints}\n请生成 {req.layers} 层系统图。"
    data = chat_json(SYSTEM_PROMPT.format(layers=req.layers), user)

    nodes: list[TreeNode] = []
    for n in data.get("nodes", []):
        try:
            payoff = int(n.get("payoff", 0) or 0)
            feas = int(n.get("feasibility", 0) or 0)
            prio = ""
            if n.get("is_leaf"):
                score = payoff * feas
                prio = "P1" if score >= 16 else ("P2" if score >= 9 else "P3")
            nodes.append(TreeNode(
                id=n.get("id", ""),
                label=n.get("label", ""),
                level=int(n.get("level", 0)),
                parent=n.get("parent"),
                smart=n.get("smart", ""),
                payoff=max(0, min(5, payoff)),
                feasibility=max(0, min(5, feas)),
                priority=prio,
                is_leaf=bool(n.get("is_leaf", False)),
            ))
        except Exception:
            continue

    return TreeResponse(
        topic=req.topic,
        nodes=nodes,
        mece_check=list(data.get("mece_check", []))[:10],
        summary=data.get("summary", ""),
        recommendations=list(data.get("recommendations", []))[:8],
    )


register(ToolMeta(
    key="tree",
    name="系统图",
    category="新QC七大手法",
    description="把大目标层层拆到可执行行动, 叶节点 SMART 化 + 优先级排序。",
    icon="Grid",
))
