# QCKit · LLM 驱动的质量工具箱

> 让 QC 手法从「填 Excel 模板」升级为「输入几个节点，LLM 自动出图 + 出报告」。

![status](https://img.shields.io/badge/status-alpha-orange) ![license](https://img.shields.io/badge/license-MIT-blue) ![python](https://img.shields.io/badge/python-3.10+-blue)

## ✨ 特性

- 🧠 **LLM 增强**：兼容 OpenAI 协议，可接 DeepSeek / 通义 / Moonshot / 本地 vLLM
- 🎨 **可视化优先**：Cytoscape / ECharts 出图，一键导出 PNG / JSON
- 📦 **本地部署友好**：`docker-compose up` 即用，配置在网页里点点填好
- 🔌 **可扩展**：新增一个工具 = 一个目录 + 一个路由，见 `docs/ADDING_A_TOOL.md`

## 🛠 已内置工具

| 分类 | 工具 | 状态 |
|---|---|---|
| 新QC七大手法 | 关联图 Relations Diagram | ✅ |
| 新QC七大手法 | 亲和图 KJ / 系统图 / 矩阵图 / PDPC | 🚧 规划中 |
| QC七大手法 | 鱼骨图 / 柏拉图 / 直方图 / 散布图 / 控制图 | 🚧 规划中 |

## 🚀 快速开始

### 方式 A：Docker（推荐）

```bash
git clone git@github.com:yidingwanglnsy-boop/qckit.git
cd qckit
# 前端先构建一次（见下方"从源码构建"），或等待预构建镜像
cp .env.example .env    # 填入 LLM key
docker compose up -d
# 打开 http://localhost:8000
```

### 方式 B：本地开发（前后端分离）

```bash
# 后端
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn qckit.main:app --reload   # :8000

# 前端（另一个终端）
cd frontend
npm install
npm run dev                        # :5173
```

浏览器打开 http://localhost:5173 ，进入「LLM 配置」填 Base URL / Key / Model，就可以用了。

### 方式 C：一体化打包

```bash
cd frontend && npm run build       # 会写入 ../backend/static
cd ../backend && uvicorn qckit.main:app
# 前后端都在 http://localhost:8000
```

## ⚙️ LLM 配置

三种方式，优先级从高到低：

1. 环境变量：`QCKIT_LLM_BASE_URL` / `QCKIT_LLM_API_KEY` / `QCKIT_LLM_MODEL`（也认 `OPENAI_*`）
2. Web 界面「LLM 配置」页
3. `~/.qckit/config.yaml`

## 📸 关联图示例

输入：问题主题 + 8 个候选原因节点 → 5 秒后得到：
- 每个节点的角色分类（核心/关键/传导/一般）+ 判定依据
- 节点之间的因果边（含强度与说明）
- 整体解读 + 3~5 条针对核心节点的改善建议
- 一张可交互、可导出 PNG 的关联图

## 🧩 新增一个 QC 工具

见 [`docs/ADDING_A_TOOL.md`](docs/ADDING_A_TOOL.md)。三步：
1. 在 `backend/qckit/tools/<name>/` 写 service.py（prompt + Pydantic 模型 + register）
2. 在 `backend/qckit/api/tools_api.py` 加一个路由
3. 在 `frontend/src/views/` 加一个页面，注册路由

## 📄 License

MIT © 2026
