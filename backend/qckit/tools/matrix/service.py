"""矩阵图（Matrix Diagram / L 型）—— 两组因素的关系强度。

典型场景: QFD 质量屋、因果 × 对策矩阵、责任 RACI。
LLM 一次性推断整张矩阵 + 每格依据 + Top 关键交叉点。
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register


class MatrixRequest(BaseModel):
    topic: str = Field(..., description="矩阵主题")
    row_label: str = Field("行(需求/原因)", description="行组标签")
    col_label: str = Field("列(特性/对策)", description="列组标签")
    rows: list[str] = Field(..., min_length=2, description="行元素")
    cols: list[str] = Field(..., min_length=2, description="列元素")
    context: str | None = None


class Cell(BaseModel):
    row: str
    col: str
    strength: int = 0        # 0/1/3/9 (标准 QFD 强度)
    symbol: str = ""         # ●=9 ◎=3 △=1
    reason: str = ""


class MatrixResponse(BaseModel):
    topic: str
    rows: list[str]
    cols: list[str]
    row_weights: dict[str, int] = {}     # 行权重 1-5
    cells: list[Cell]
    hot_spots: list[dict] = []           # Top 交叉点
    col_correlations: list[dict] = []    # 屋顶三角 (列-列)
    summary: str = ""
    recommendations: list[str] = []


SYSTEM_PROMPT = """你是 QC 新七大手法「矩阵图法」专家, 精通 QFD 质量屋。
输入两组因素, 判断每对交叉的关联强度:
- 9 = 强关联 (●)
- 3 = 中关联 (◎)
- 1 = 弱关联 (△)
- 0 = 无关联 (留空)

同时:
1. 给出每行的权重 1-5 (基于业务重要性)
2. 找出 Top 5 关键交叉点 (强度*权重最高)
3. 列-列相关性 (屋顶三角): +2/-2 强正/负相关, +1/-1 弱, 0 无关

严格返回 JSON:
{
  "row_weights": {"行1": 5, "行2": 3, ...},
  "cells": [{"row":"...","col":"...","strength":9,"reason":"20字内依据"}],
  "hot_spots":[{"row":"...","col":"...","score":45,"action":"20字建议"}],
  "col_correlations":[{"col1":"...","col2":"...","corr":+2,"reason":"..."}],
  "summary":"整张矩阵解读 100 字",
  "recommendations":["Top 5 交叉点里最应立即做的 3 条"]
}
"""


def _symbol(s: int) -> str:
    return {9: "●", 3: "◎", 1: "△"}.get(s, "")


def analyze(req: MatrixRequest) -> MatrixResponse:
    ctx = f"\n背景: {req.context}" if req.context else ""
    user = (f"主题: {req.topic}{ctx}\n"
            f"{req.row_label}({len(req.rows)}): {', '.join(req.rows)}\n"
            f"{req.col_label}({len(req.cols)}): {', '.join(req.cols)}")
    data = chat_json(SYSTEM_PROMPT, user)

    row_set, col_set = set(req.rows), set(req.cols)
    cells = []
    for c in data.get("cells", []):
        r, co = c.get("row"), c.get("col")
        if r in row_set and co in col_set:
            s = int(c.get("strength", 0) or 0)
            s = 9 if s >= 7 else (3 if s >= 2 else (1 if s == 1 else 0))
            if s > 0:
                cells.append(Cell(row=r, col=co, strength=s,
                                  symbol=_symbol(s),
                                  reason=c.get("reason", "")))

    weights = {r: max(1, min(5, int(v))) for r, v in
               data.get("row_weights", {}).items() if r in row_set}

    return MatrixResponse(
        topic=req.topic,
        rows=req.rows, cols=req.cols,
        row_weights=weights,
        cells=cells,
        hot_spots=list(data.get("hot_spots", []))[:8],
        col_correlations=list(data.get("col_correlations", []))[:20],
        summary=data.get("summary", ""),
        recommendations=list(data.get("recommendations", []))[:8],
    )


register(ToolMeta(
    key="matrix",
    name="矩阵图",
    category="新QC七大手法",
    description="两组因素关系强度矩阵 (QFD/RACI/因果对策), AI 一次性推断整张矩阵。",
    icon="Grid",
))
