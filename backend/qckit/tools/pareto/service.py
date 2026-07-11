"""柏拉图（Pareto Diagram / 80-20 分析）。

核心：纯数学，不依赖 LLM。用户给数据即可画图。
LLM 洞察为可选加成（use_llm=False 时完全不调 LLM）。
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register


class ParetoItemIn(BaseModel):
    name: str
    value: float


class ParetoRequest(BaseModel):
    topic: str = Field(..., description="分析主题")
    metric: str = Field("频次", description="度量单位")
    items: list[ParetoItemIn] = Field(..., min_length=2)
    threshold: float = Field(80.0, ge=1.0, le=99.0, description="关键少数累计占比阈值 %")
    use_llm: bool = Field(False, description="是否调用 LLM 生成洞察与建议")
    context: str | None = None


class ParetoItemOut(BaseModel):
    name: str
    value: float
    percent: float
    cumulative_percent: float
    is_vital_few: bool


class ParetoResponse(BaseModel):
    topic: str
    metric: str
    threshold: float
    total: float
    items: list[ParetoItemOut]
    vital_few: list[str]
    insights: str = ""
    recommendations: list[str] = []


SYSTEM = """你是 QC 顾问，擅长柏拉图（Pareto）分析。用户已给出排序数据与关键少数（后端计算），
你只需给出：
- insights: 关键少数背后的可能根因或规律（150 字内）
- recommendations: 3-5 条针对关键少数的可执行改善方向

严格返回 JSON：
{"insights": "...", "recommendations": ["..."]}"""


def analyze(req: ParetoRequest) -> ParetoResponse:
    # 1. 纯数学：排序 + 占比 + 累计 + 关键少数标记
    sorted_items = sorted(req.items, key=lambda x: x.value, reverse=True)
    total = sum(x.value for x in sorted_items) or 1.0
    threshold = float(req.threshold)

    out_items: list[ParetoItemOut] = []
    vital_names: list[str] = []
    crossed = False
    cum = 0.0
    for it in sorted_items:
        pct = it.value / total * 100
        cum += pct
        # 关键少数 = 累计尚未越过阈值的 + 越过阈值的那一项本身
        if not crossed:
            is_vf = True
            vital_names.append(it.name)
            if cum >= threshold:
                crossed = True
        else:
            is_vf = False
        out_items.append(ParetoItemOut(
            name=it.name, value=it.value, percent=round(pct, 2),
            cumulative_percent=round(cum, 2), is_vital_few=is_vf,
        ))

    # 2. LLM 洞察（可选）
    insights, recs = "", []
    if req.use_llm:
        lines = "\n".join(f"- {i.name}: {i.value} ({i.percent}%, 累计 {i.cumulative_percent}%)"
                          for i in out_items)
        user = f"""主题：{req.topic}
度量：{req.metric}
阈值：{threshold}%
背景：{req.context or "（无）"}
关键少数：{', '.join(vital_names)}

排序后数据：
{lines}

按 system schema 输出 JSON。"""
        try:
            data = chat_json(SYSTEM, user)
            insights = data.get("insights", "")
            recs = list(data.get("recommendations", []))[:8]
        except Exception as e:
            insights = f"（LLM 分析失败：{e}）"

    return ParetoResponse(
        topic=req.topic, metric=req.metric, threshold=threshold,
        total=round(total, 2), items=out_items,
        vital_few=vital_names, insights=insights, recommendations=recs,
    )


register(ToolMeta(
    key="pareto",
    name="柏拉图",
    category="QC七大手法",
    description="按频次/成本降序，找出贡献 ≥阈值 的关键少数（Vital Few）。",
    icon="TrendCharts",
))
