"""关联图（Relations Diagram）工具。

输入：问题主题 + 候选节点列表
输出：
  - 每个节点的分类：核心/关键/传导/一般
  - 节点之间的因果关系边
  - 附带分析说明
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register


NodeRole = Literal["core", "key", "conduct", "normal"]


class RelationsRequest(BaseModel):
    topic: str = Field(..., description="要分析的核心问题/主题")
    nodes: list[str] = Field(..., min_length=2, description="用户提供的候选节点")
    context: str | None = Field(None, description="补充背景信息，可选")


class NodeOut(BaseModel):
    id: str
    label: str
    role: NodeRole
    reason: str = ""
    in_degree: int = 0
    out_degree: int = 0


class EdgeOut(BaseModel):
    source: str
    target: str
    label: str = ""      # 因果说明
    strength: int = 1    # 1-3 强度


class RelationsResponse(BaseModel):
    topic: str
    nodes: list[NodeOut]
    edges: list[EdgeOut]
    summary: str
    recommendations: list[str] = []


SYSTEM_PROMPT = """你是精通质量管理与 QC 新旧七大手法的顾问，尤其擅长「关联图法（Relations Diagram）」。
关联图法用于分析复杂问题中各原因之间的因果与关联关系，找出核心原因。

节点角色定义：
- core（核心节点）：问题的根源/根本原因，通常出度高、入度低，是需要重点改善的对象。一般 1-3 个。
- key（关键节点）：重要中间原因，同时受多方影响并影响多方（出入度都较高）。
- conduct（传导节点）：把上游原因传导到下游的中间环节（出度 ≈ 入度，中等）。
- normal（一般节点）：影响面较窄的次要因素。

必须严格返回 JSON，schema：
{
  "nodes": [{"id": "n1", "label": "...", "role": "core|key|conduct|normal", "reason": "为何归为此类"}],
  "edges": [{"source": "n1", "target": "n2", "label": "因果说明", "strength": 1|2|3}],
  "summary": "对整张关联图的整体解读（150 字内）",
  "recommendations": ["改善建议1", "改善建议2", "..."]
}

规则：
1. id 使用传入顺序对应的 n1/n2/... 编号。
2. 只在真实存在明显因果/相关时才连边，避免全连接。
3. label 必须用中文；strength：1=弱，2=中，3=强。
4. 每个节点必须给出 role 和 reason。
5. recommendations 输出 3-5 条针对 core 节点的可执行改善方向。
"""


def analyze(req: RelationsRequest) -> RelationsResponse:
    node_lines = "\n".join(f"n{i+1}. {n}" for i, n in enumerate(req.nodes))
    user_prompt = f"""问题主题：{req.topic}

补充背景：{req.context or "（无）"}

候选节点：
{node_lines}

请按 system 中的 schema 返回 JSON。"""

    data = chat_json(SYSTEM_PROMPT, user_prompt)

    # 组装 & 校验
    id_map = {f"n{i+1}": label for i, label in enumerate(req.nodes)}
    nodes_raw = {n["id"]: n for n in data.get("nodes", [])}
    edges_raw = data.get("edges", [])

    nodes: list[NodeOut] = []
    for nid, label in id_map.items():
        info = nodes_raw.get(nid, {})
        nodes.append(NodeOut(
            id=nid,
            label=label,
            role=_safe_role(info.get("role")),
            reason=info.get("reason", ""),
        ))

    edges: list[EdgeOut] = []
    valid_ids = set(id_map)
    for e in edges_raw:
        s, t = e.get("source"), e.get("target")
        if s in valid_ids and t in valid_ids and s != t:
            edges.append(EdgeOut(
                source=s, target=t,
                label=e.get("label", ""),
                strength=_clamp(int(e.get("strength", 1) or 1), 1, 3),
            ))

    # 计算出入度（可用于前端角色校验展示）
    deg_in = {n.id: 0 for n in nodes}
    deg_out = {n.id: 0 for n in nodes}
    for e in edges:
        deg_out[e.source] += 1
        deg_in[e.target] += 1
    for n in nodes:
        n.in_degree = deg_in[n.id]
        n.out_degree = deg_out[n.id]

    return RelationsResponse(
        topic=req.topic,
        nodes=nodes,
        edges=edges,
        summary=data.get("summary", ""),
        recommendations=list(data.get("recommendations", []))[:8],
    )


def _safe_role(v) -> NodeRole:
    if v in ("core", "key", "conduct", "normal"):
        return v  # type: ignore
    return "normal"


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


register(ToolMeta(
    key="relations",
    name="关联图",
    category="新QC七大手法",
    description="分析复杂问题中各原因间的因果与关联，识别核心/关键/传导节点。",
    icon="Share",
))
