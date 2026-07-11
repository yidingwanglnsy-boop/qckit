"""FastAPI 入口: uvicorn qckit.main:app --reload"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.brand_api import router as brand_router
from .api.config_api import router as config_router
from .api.tools_api import router as tools_router
from .tools import *  # noqa: F401,F403  触发工具注册


app = FastAPI(title="QCKit", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_router)
app.include_router(brand_router)
app.include_router(tools_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# 生产模式：如果 backend/static 存在（构建好的前端），一并托管
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        target = STATIC_DIR / full_path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(STATIC_DIR / "index.html")
