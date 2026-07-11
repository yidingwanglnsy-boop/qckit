from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..core.registry import all_tools
from ..core.pptx_export import (build_affinity_pptx, build_pareto_pptx,
                                build_radar_pptx, build_relations_pptx,
                                build_w5h2_pptx)
from ..tools.affinity import AffinityRequest, analyze as affinity_analyze
from ..tools.pareto import ParetoRequest, analyze as pareto_analyze
from ..tools.radar import RadarRequest, analyze as radar_analyze
from ..tools.relations import RelationsRequest, analyze as relations_analyze
from ..tools.w5h2 import W5H2Request, analyze as w5h2_analyze

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("")
def list_tools() -> list[dict]:
    return [t.__dict__ for t in all_tools()]


def _run(fn, req):
    try:
        return fn(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 分析失败: {e}") from e


def _pptx_response(buf, filename: str) -> StreamingResponse:
    quoted = quote(filename)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quoted}"},
    )


@router.post("/relations/analyze")
def relations_endpoint(req: RelationsRequest):
    return _run(relations_analyze, req)


@router.post("/relations/export/pptx")
def relations_export_pptx(payload: dict):
    buf = build_relations_pptx(payload)
    topic = payload.get("topic", "关联图")
    return _pptx_response(buf, f"关联图_{topic}.pptx")


@router.post("/affinity/analyze")
def affinity_endpoint(req: AffinityRequest):
    return _run(affinity_analyze, req)


@router.post("/affinity/export/pptx")
def affinity_export_pptx(payload: dict):
    buf = build_affinity_pptx(payload)
    topic = payload.get("topic", "亲和图")
    return _pptx_response(buf, f"亲和图_{topic}.pptx")


@router.post("/pareto/analyze")
def pareto_endpoint(req: ParetoRequest):
    return _run(pareto_analyze, req)


@router.post("/pareto/export/pptx")
def pareto_export_pptx(payload: dict):
    buf = build_pareto_pptx(payload)
    topic = payload.get("topic", "柏拉图")
    return _pptx_response(buf, f"柏拉图_{topic}.pptx")


@router.post("/radar/analyze")
def radar_endpoint(req: RadarRequest):
    return _run(radar_analyze, req)


@router.post("/radar/export/pptx")
def radar_export_pptx(payload: dict):
    buf = build_radar_pptx(payload)
    topic = payload.get("topic", "雷达图")
    return _pptx_response(buf, f"雷达图_{topic}.pptx")


@router.post("/w5h2/analyze")
def w5h2_endpoint(req: W5H2Request):
    return _run(w5h2_analyze, req)


@router.post("/w5h2/export/pptx")
def w5h2_export_pptx(payload: dict):
    buf = build_w5h2_pptx(payload)
    topic = payload.get("topic", "5W2H")
    return _pptx_response(buf, f"5W2H_{topic}.pptx")
