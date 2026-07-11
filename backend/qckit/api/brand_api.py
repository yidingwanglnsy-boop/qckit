from fastapi import APIRouter, HTTPException

from ..brand import BrandConfig, PRESETS, get_brand, set_brand

router = APIRouter(prefix="/api/brand", tags=["brand"])


@router.get("")
def read_brand() -> dict:
    return {
        "current": get_brand().model_dump(),
        "presets": {k: v.model_dump() for k, v in PRESETS.items()},
    }


@router.post("")
def update_brand(payload: BrandConfig) -> dict:
    set_brand(payload)
    return {"ok": True, "current": payload.model_dump()}


@router.post("/reset")
def reset_brand(preset: str = "default") -> dict:
    if preset not in PRESETS:
        raise HTTPException(400, f"未知预设: {preset}")
    cfg = PRESETS[preset].model_copy()
    set_brand(cfg)
    return {"ok": True, "current": cfg.model_dump()}
