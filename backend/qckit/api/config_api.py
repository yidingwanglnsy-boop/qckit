from fastapi import APIRouter

from ..config import AppConfig, LLMConfig, get_config, set_config

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("")
def read_config() -> dict:
    cfg = get_config()
    d = cfg.model_dump()
    # 掩码 api_key
    key = d["llm"].get("api_key") or ""
    if key:
        d["llm"]["api_key"] = key[:4] + "*" * max(0, len(key) - 8) + key[-4:]
    return d


@router.post("")
def update_config(payload: LLMConfig) -> dict:
    cfg = get_config()
    # 保留旧 key 如果新值是掩码 (含 * 或 …) 或空
    if not payload.api_key or "*" in payload.api_key or "…" in payload.api_key:
        payload.api_key = cfg.llm.api_key
    new_cfg = AppConfig(llm=payload)
    set_config(new_cfg)
    return {"ok": True}
