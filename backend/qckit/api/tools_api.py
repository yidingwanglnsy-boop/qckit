from fastapi import APIRouter, HTTPException

from ..core.registry import all_tools
from ..tools.relations import RelationsRequest, analyze as relations_analyze

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("")
def list_tools() -> list[dict]:
    return [t.__dict__ for t in all_tools()]


@router.post("/relations/analyze")
def relations_endpoint(req: RelationsRequest):
    try:
        return relations_analyze(req)
    except Exception as e:  # 让前端拿到清晰错误
        raise HTTPException(status_code=500, detail=f"LLM 分析失败: {e}") from e
