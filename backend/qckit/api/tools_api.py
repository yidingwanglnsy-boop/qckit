from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..brand import get_brand
from ..core.fishbone_pptx import build_fishbone_pptx
from ..core.registry import all_tools
from ..core.pptx_export import (build_affinity_pptx, build_arrow_pptx,
                                build_matrix_pptx, build_mda_pptx,
                                build_pareto_pptx, build_pdpc_pptx,
                                build_radar_pptx, build_rca_pptx,
                                build_relations_pptx, build_tree_pptx,
                                build_w5h2_pptx)
from ..core.xlsx_export import build_rca_xlsx, build_w5h2_xlsx
from ..tools.affinity import AffinityRequest, analyze as affinity_analyze
from ..tools.arrow import ArrowRequest, analyze as arrow_analyze
from ..tools.fishbone import FishboneRequest, analyze as fishbone_analyze
from ..tools.matrix import MatrixRequest, analyze as matrix_analyze
from ..tools.mda import MDARequest, analyze as mda_analyze
from ..tools.pareto import ParetoRequest, analyze as pareto_analyze
from ..tools.pdpc import PDPCRequest, analyze as pdpc_analyze
from ..tools.qcc_guide import GuideRequest, analyze as guide_analyze
from ..tools.radar import RadarRequest, analyze as radar_analyze
from ..tools.rca import RcaRequest, analyze as rca_analyze
from ..tools.relations import RelationsRequest, analyze as relations_analyze
from ..tools.tree import TreeRequest, analyze as tree_analyze
from ..tools.w5h2 import W5H2Request, analyze as w5h2_analyze

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("")
def list_tools() -> list[dict]:
    return [t.__dict__ for t in all_tools()]


import logging
from openai import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError

logger = logging.getLogger("qckit.tools")


def _run(fn, req):
    """分类错误 + 结构化返回, 前端可据 error_code 精细化 UI."""
    try:
        return fn(req)
    except APITimeoutError as e:
        logger.warning("LLM timeout: %s", e)
        raise HTTPException(504, detail={
            "error_code": "LLM_TIMEOUT",
            "message": "AI 响应超时。请稍后重试，或缩小输入范围。",
            "hint": "若经常超时可在「设置」里调大 timeout。",
        })
    except APIConnectionError as e:
        logger.warning("LLM connect fail: %s", e)
        raise HTTPException(503, detail={
            "error_code": "LLM_UNREACHABLE",
            "message": "无法连接 AI 服务。请检查网络或 base_url。",
            "hint": "打开「设置」核对 base_url。",
        })
    except AuthenticationError as e:
        logger.warning("LLM auth fail: %s", e)
        raise HTTPException(401, detail={
            "error_code": "LLM_AUTH",
            "message": "API Key 无效或过期。",
            "hint": "去「设置」重新填写 api_key。",
        })
    except RateLimitError as e:
        logger.warning("LLM rate limit: %s", e)
        raise HTTPException(429, detail={
            "error_code": "LLM_RATE_LIMIT",
            "message": "AI 服务限流，稍后再试。",
            "hint": "换个模型或等 30s 再试。",
        })
    except ValueError as e:
        # _safe_json 抛的
        logger.warning("LLM bad JSON: %s", str(e)[:300])
        raise HTTPException(502, detail={
            "error_code": "LLM_BAD_JSON",
            "message": "AI 返回格式异常，无法解析。",
            "hint": "点「重试」重新生成；若持续失败可换个模型。诊断日志已保存到 ~/.qckit/last_llm_debug.txt",
            "raw_preview": str(e)[:400],
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Tool run failed")
        raise HTTPException(500, detail={
            "error_code": "INTERNAL",
            "message": f"分析失败: {type(e).__name__}",
            "hint": "查看后端日志 ~/.qckit/qckit.log",
        })


def _pptx_response(buf, filename: str) -> StreamingResponse:
    quoted = quote(filename)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quoted}"},
    )


def _xlsx_response(buf, filename: str) -> StreamingResponse:
    quoted = quote(filename)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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


@router.post("/w5h2/export/xlsx")
def w5h2_export_xlsx(payload: dict):
    buf = build_w5h2_xlsx(payload, get_brand())
    topic = payload.get("topic", "5W2H")
    return _xlsx_response(buf, f"5W2H_{topic}.xlsx")


@router.post("/rca/analyze")
def rca_endpoint(req: RcaRequest):
    return _run(rca_analyze, req)


@router.post("/rca/export/pptx")
def rca_export_pptx(payload: dict):
    buf = build_rca_pptx(payload)
    topic = payload.get("topic", "根因确认")
    return _pptx_response(buf, f"根因确认_{topic}.pptx")


@router.post("/rca/export/xlsx")
def rca_export_xlsx(payload: dict):
    buf = build_rca_xlsx(payload, get_brand())
    topic = payload.get("topic", "根因确认")
    return _xlsx_response(buf, f"根因确认_{topic}.xlsx")


@router.post("/fishbone/analyze")
def fishbone_endpoint(req: FishboneRequest):
    return _run(fishbone_analyze, req)


@router.post("/fishbone/export/pptx")
def fishbone_export_pptx(payload: dict):
    buf = build_fishbone_pptx(payload, get_brand())
    topic = payload.get("topic", "鱼骨图")
    return _pptx_response(buf, f"鱼骨图_{topic}.pptx")


@router.post("/qcc_guide/analyze")
def qcc_guide_endpoint(req: GuideRequest):
    return _run(guide_analyze, req)


# —— 新 5 工具 ——————————————————————————————————————————————
@router.post("/tree/analyze")
def tree_endpoint(req: TreeRequest):
    return _run(tree_analyze, req)


@router.post("/tree/export/pptx")
def tree_export_pptx(payload: dict):
    buf = build_tree_pptx(payload)
    topic = payload.get("topic", "系统图")
    return _pptx_response(buf, f"系统图_{topic}.pptx")


@router.post("/matrix/analyze")
def matrix_endpoint(req: MatrixRequest):
    return _run(matrix_analyze, req)


@router.post("/matrix/export/pptx")
def matrix_export_pptx(payload: dict):
    buf = build_matrix_pptx(payload)
    topic = payload.get("topic", "矩阵图")
    return _pptx_response(buf, f"矩阵图_{topic}.pptx")


@router.post("/mda/analyze")
def mda_endpoint(req: MDARequest):
    return _run(mda_analyze, req)


@router.post("/mda/export/pptx")
def mda_export_pptx(payload: dict):
    buf = build_mda_pptx(payload)
    topic = payload.get("topic", "矩阵数据解析")
    return _pptx_response(buf, f"矩阵数据解析_{topic}.pptx")


@router.post("/pdpc/analyze")
def pdpc_endpoint(req: PDPCRequest):
    return _run(pdpc_analyze, req)


@router.post("/pdpc/export/pptx")
def pdpc_export_pptx(payload: dict):
    buf = build_pdpc_pptx(payload)
    topic = payload.get("topic", "PDPC")
    return _pptx_response(buf, f"PDPC_{topic}.pptx")


@router.post("/arrow/analyze")
def arrow_endpoint(req: ArrowRequest):
    return _run(arrow_analyze, req)


@router.post("/arrow/export/pptx")
def arrow_export_pptx(payload: dict):
    buf = build_arrow_pptx(payload)
    topic = payload.get("topic", "箭线图")
    return _pptx_response(buf, f"箭线图_{topic}.pptx")
