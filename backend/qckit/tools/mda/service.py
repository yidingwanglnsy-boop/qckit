"""矩阵数据解析法（Matrix Data Analysis / 简化 PCA）—— N7 唯一定量工具。

对象 × 指标数据表, 降到 2D 主成分空间, LLM 解读象限。
"""
from __future__ import annotations

import math

from pydantic import BaseModel, Field

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register


class MDARequest(BaseModel):
    topic: str = Field(..., description="分析主题")
    metric_names: list[str] = Field(..., min_length=2, description="指标名列表")
    subjects: list[dict] = Field(..., min_length=2,
        description="对象数据 [{name, values:[v1,v2,...]}]")
    lower_is_better: list[str] | None = Field(None,
        description="越低越好的指标名 (如 价格/工期), 自动反向归一")


class MDAPoint(BaseModel):
    name: str
    pc1: float
    pc2: float
    quadrant: int      # 1/2/3/4


class MDAResponse(BaseModel):
    topic: str
    metric_names: list[str]
    pc1_name: str = "综合实力"
    pc2_name: str = "性价比倾向"
    variance_ratio: list[float] = []   # 两根主轴解释度
    points: list[MDAPoint]
    quadrant_labels: dict[str, str] = {}    # 1/2/3/4 -> 象限文字标签
    quadrant_insights: dict[str, str] = {}  # 每象限 LLM 解读
    recommendations: list[str] = []


def _z_score(vals: list[float]) -> list[float]:
    if not vals:
        return []
    mu = sum(vals) / len(vals)
    var = sum((v - mu) ** 2 for v in vals) / len(vals)
    sd = math.sqrt(var) if var > 0 else 1.0
    return [(v - mu) / sd for v in vals]


def _pca_2d(matrix: list[list[float]]) -> tuple[list[list[float]], list[float]]:
    """朴素 2D PCA: 幂迭代 + 二次去除. 返回投影坐标 + 各轴方差解释率。"""
    n = len(matrix)
    if n < 2:
        return [[0.0, 0.0] for _ in matrix], [0.0, 0.0]
    m = len(matrix[0])
    # 协方差矩阵 (m x m)
    means = [sum(row[j] for row in matrix) / n for j in range(m)]
    cov = [[0.0]*m for _ in range(m)]
    for row in matrix:
        for i in range(m):
            for j in range(m):
                cov[i][j] += (row[i]-means[i])*(row[j]-means[j])
    for i in range(m):
        for j in range(m):
            cov[i][j] /= max(n-1, 1)

    def mv(A, v):
        return [sum(A[i][k]*v[k] for k in range(len(v))) for i in range(len(A))]
    def norm(v):
        s = math.sqrt(sum(x*x for x in v)) or 1.0
        return [x/s for x in v]
    def power(A, iters=60):
        v = [1.0/math.sqrt(m)] * m
        for _ in range(iters):
            v = norm(mv(A, v))
        lam = sum(v[i]*sum(A[i][k]*v[k] for k in range(m)) for i in range(m))
        return v, lam
    v1, lam1 = power(cov)
    # 去除 v1 分量
    cov2 = [[cov[i][j] - lam1*v1[i]*v1[j] for j in range(m)] for i in range(m)]
    v2, lam2 = power(cov2)

    projected = []
    for row in matrix:
        centered = [row[j]-means[j] for j in range(m)]
        pc1 = sum(centered[j]*v1[j] for j in range(m))
        pc2 = sum(centered[j]*v2[j] for j in range(m))
        projected.append([pc1, pc2])
    total = lam1 + lam2 + 1e-9
    return projected, [lam1/total, lam2/total]


SYSTEM_PROMPT = """你是 QC 新七大手法「矩阵数据解析法」专家。
用户完成了 2D PCA, 你需要:
1. 为两根主成分命名 (如 pc1="综合实力", pc2="性价比倾向")
2. 为 4 个象限打自然语言标签 (如 "第 I 象限=高质高效")
3. 为每象限的对象给一段解读 + 定位建议
严格 JSON:
{"pc1_name":"...","pc2_name":"...",
 "quadrant_labels":{"1":"...","2":"...","3":"...","4":"..."},
 "quadrant_insights":{"1":"该象限对象适合...","2":"...","3":"...","4":"..."},
 "recommendations":["决策建议 1","建议 2","建议 3"]}
"""


def analyze(req: MDARequest) -> MDAResponse:
    # 组装原始矩阵
    m = len(req.metric_names)
    matrix: list[list[float]] = []
    names: list[str] = []
    for s in req.subjects:
        vals = s.get("values") or []
        if len(vals) != m:
            continue
        try:
            matrix.append([float(v) for v in vals])
            names.append(str(s.get("name", "?")))
        except (TypeError, ValueError):
            continue
    if len(matrix) < 2:
        return MDAResponse(topic=req.topic, metric_names=req.metric_names, points=[])

    # 反向指标处理: 越低越好的取负
    low_set = set(req.lower_is_better or [])
    for j, name in enumerate(req.metric_names):
        if name in low_set:
            for row in matrix:
                row[j] = -row[j]

    # 按列 z-score 归一
    for j in range(m):
        col = [row[j] for row in matrix]
        z = _z_score(col)
        for i, v in enumerate(z):
            matrix[i][j] = v

    proj, var = _pca_2d(matrix)
    points = []
    for name, (p1, p2) in zip(names, proj):
        q = 1 if (p1 >= 0 and p2 >= 0) else \
            2 if (p1 < 0 and p2 >= 0) else \
            3 if (p1 < 0 and p2 < 0) else 4
        points.append(MDAPoint(name=name, pc1=round(p1, 3),
                               pc2=round(p2, 3), quadrant=q))

    # 让 LLM 解读
    quadrant_summary = {q: [p.name for p in points if p.quadrant == q]
                        for q in (1, 2, 3, 4)}
    user = (f"主题: {req.topic}\n指标: {req.metric_names}\n"
            f"各象限对象: {quadrant_summary}\n"
            f"两根主成分方差解释度: {[round(v,2) for v in var]}")
    data = chat_json(SYSTEM_PROMPT, user)

    return MDAResponse(
        topic=req.topic,
        metric_names=req.metric_names,
        pc1_name=data.get("pc1_name", "综合实力"),
        pc2_name=data.get("pc2_name", "性价比倾向"),
        variance_ratio=[round(v, 3) for v in var],
        points=points,
        quadrant_labels={str(k): v for k, v in data.get("quadrant_labels", {}).items()},
        quadrant_insights={str(k): v for k, v in data.get("quadrant_insights", {}).items()},
        recommendations=list(data.get("recommendations", []))[:8],
    )


register(ToolMeta(
    key="mda",
    name="矩阵数据解析",
    category="新QC七大手法",
    description="多对象 × 多指标数据 2D 主成分降维, AI 自动解读象限定位。",
    icon="DataAnalysis",
))
