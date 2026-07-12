# ═══════════════════════════════════════════════════════════
# QCKit 多阶段 Dockerfile —— 前端 build + 后端 install 一体化
# ═══════════════════════════════════════════════════════════

# 阶段 1: 前端构建
FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build   # 产物落在 ../backend/static

# 阶段 2: 后端运行时
FROM python:3.11-slim
WORKDIR /app

# 系统依赖 (python-pptx 需要, curl 用于健康检查)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl fonts-noto-cjk fonts-noto-cjk-extra \
    && rm -rf /var/lib/apt/lists/*

# 后端依赖
COPY backend/pyproject.toml backend/pyproject.toml
COPY backend/qckit backend/qckit
RUN pip install --no-cache-dir -e ./backend

# 前端产物 (由 stage 1 输出的 backend/static)
COPY --from=frontend /backend/static /app/backend/static

# 数据卷: 用户配置/项目/历史
VOLUME ["/root/.qckit"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -sf http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "qckit.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]
