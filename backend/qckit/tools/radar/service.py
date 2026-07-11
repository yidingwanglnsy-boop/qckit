"""雷达图（Radar Chart）—— 多对象多维度对比评估。

用途：供应商评估、团队体检、5S 打分、产品竞品对比…
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register


class RadarEntity(BaseModel):
    name: str
    scores: list[float]  # 与 dimensions 一一对应


class RadarRequest(BaseModel):
    topic: str = Field(..., description="评估主题（如：Q3 供应商综合评估）")
    dimensions: list[str] = Field(..., min_length=3, max_length=12)
    entities: list[RadarEntity] = Field(..., min_length=1, max_length=6)
    max_score: float = Field(10.0, ge=1.0, le=100.0, description="满分（每维度）")
    weak_threshold: float = Field(0.6, ge=0.1, le=0.95,
                                  description="短板阈值 (归一化后 <此值算短板)")
    use_llm: bool = Field(False)
    context: str | None = None

    @model_validator(mode="after")
    def _match_len(self):
        n = len(self.dimensions)
        for e in self.entities:
            if len(e.scores) != n:
                raise ValueError(f"实体 {e.name} 的分数数量 {len(e.scores)} != 维度数 {n}")
        return self


class RadarEntityOut(BaseModel):
    name: str
    scores: list[float]
    average: float
    weak_dims: list[str]   # 短板维度


class RadarResponse(BaseModel):
    topic: str
    dimensions: list[str]
    max_score: float
    weak_threshold: float
    entities: list[RadarEntityOut]
    best_entity: str      # 平均分最高
    dim_leaders: dict[str, str]  # 每维度最强者
    insights: str = ""
    recommendations: list[str] = []


SYSTEM = """你是 QC 顾问，擅长多维评估分析。用户已给出维度、多个对象、和打分矩阵；
后端已算出平均分、短板维度、各维度冠军。请给出：
- insights: 关键对比洞察（谁在哪方面强/弱，为何，200 字内）
- recommendations: 3-5 条针对短板的可执行改善方向

严格返回 JSON: {"insights": "...", "recommendations": ["..."]}"""


def analyze(req: RadarRequest) -> RadarResponse:
    max_s = float(req.max_score)
    weak_cut = req.weak_threshold * max_s

    entities_out: list[RadarEntityOut] = []
    for e in req.entities:
        clipped = [max(0.0, min(max_s, float(s))) for s in e.scores]
        avg = sum(clipped) / len(clipped)
        weak = [req.dimensions[i] for i, s in enumerate(clipped) if s < weak_cut]
        entities_out.append(RadarEntityOut(
            name=e.name, scores=[round(s, 2) for s in clipped],
            average=round(avg, 2), weak_dims=weak,
        ))

    best = max(entities_out, key=lambda x: x.average).name
    leaders: dict[str, str] = {}
    for i, dim in enumerate(req.dimensions):
        leader = max(entities_out, key=lambda x: x.scores[i])
        leaders[dim] = leader.name

    insights, recs = "", []
    if req.use_llm:
        lines = "对象 | " + " | ".join(req.dimensions) + " | 平均"
        rows = "\n".join(
            f"{e.name} | " + " | ".join(f"{s}" for s in e.scores) + f" | {e.average}"
            for e in entities_out
        )
        weak_txt = "\n".join(f"- {e.name} 短板: {', '.join(e.weak_dims) or '无'}"
                             for e in entities_out)
        user = f"""主题: {req.topic}
满分: {max_s} / 短板阈值: {req.weak_threshold*100:.0f}%
背景: {req.context or "（无）"}
最强: {best}

数据:
{lines}
{rows}

{weak_txt}

按 system schema 输出 JSON。"""
        try:
            data = chat_json(SYSTEM, user)
            insights = data.get("insights", "")
            recs = list(data.get("recommendations", []))[:8]
        except Exception as e:
            insights = f"（LLM 分析失败：{e}）"

    return RadarResponse(
        topic=req.topic, dimensions=req.dimensions, max_score=max_s,
        weak_threshold=req.weak_threshold, entities=entities_out,
        best_entity=best, dim_leaders=leaders,
        insights=insights, recommendations=recs,
    )


register(ToolMeta(
    key="radar",
    name="雷达图",
    category="通用工具",
    description="多维度多对象对比评估，识别强项与短板。",
    icon="Aim",
))
