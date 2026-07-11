<div align="center">

# 🛠 QCKit

**LLM 驱动的开源质量工具箱 · 让 QC 手法从「填 Excel 模板」升级为「输入几个节点，AI 自动出图 + 出报告 + 一键 PPT」**

[![status](https://img.shields.io/badge/status-alpha-orange)](https://github.com/yidingwanglnsy-boop/qckit)
[![license](https://img.shields.io/badge/license-PolyForm_NC_1.0.0-purple)](./LICENSE)
[![commercial](https://img.shields.io/badge/commercial-license_required-red)](./LICENSE)
[![python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![vue](https://img.shields.io/badge/vue-3.4-42b883)](https://vuejs.org/)

[🌐 官方主页](https://yidingwanglnsy-boop.github.io/qckit/) · [📖 快速开始](#-快速开始) · [🧰 内置工具](#-内置工具) · [🚀 演示](#-演示截图) · [💬 反馈](https://github.com/yidingwanglnsy-boop/qckit/issues)

</div>

---

## ✨ 为什么做 QCKit

传统 QC 工具的三大痛点：

- 📄 **Excel 模板疲劳** —— 每次 QCC 都在填一模一样的空白格子
- 🎨 **画图太累** —— 关联图、鱼骨图、5W2H 都要手工排版
- 📊 **汇报颜值差** —— 老板要 PPT，你却只能截 Excel 图片

**QCKit 的答案**：输入课题 → LLM 分析 → 可交互图表 → **一键导出 PPT（原生形状可编辑）+ Excel**

---

## 🧰 内置工具

| 分类 | 工具 | 能力 | 状态 |
|---|---|---|---|
| **入门指南** | 🧭 QCC 思路生成器 | 问题解决型 QCC 五阶段路线图（含推荐工具跳转） | ✅ |
| **新 QC 七大手法** | 🔗 关联图 (Relations) | LLM 分类节点角色 + 画因果边 | ✅ |
| | 🎯 亲和图 KJ (Affinity) | 发散想法自动归类 | ✅ |
| **QC 七大手法** | 🐟 鱼骨图 (4M) | 4M 分类 + 层级末端 + PPTX 原生形状 | ✅ |
| | 📊 柏拉图 (Pareto) | 80/20 关键少数分析 | ✅ |
| **通用工具** | 🕸 雷达图 (Radar) | 多维评估打分 | ✅ |
| | 📋 5W2H (W5H2) | 计划展开 + 中英对齐表头 | ✅ |
| | 🔍 根因确认 (RCA) | 5-Why 逐层推理 | ✅ |

**全部支持**：LLM 自动生成 → 手工编辑 → PPTX / XLSX / JSON 导出 → 品牌主题定制

---

## 🚀 快速开始

### 方式 A：Docker（推荐给评估用户）

```bash
git clone https://github.com/yidingwanglnsy-boop/qckit.git
cd qckit
docker compose up -d
# 打开 http://localhost:8000，在「大模型 API」页跟着 3 步向导配置
```

### 方式 B：本地开发（前后端分离）

```bash
# 后端
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn qckit.main:app --reload            # :8000

# 前端（另一个终端）
cd frontend
npm install
npm run dev                                 # :5173
```

浏览器打开 http://localhost:5173，侧边栏「**配置 → 大模型 API**」跟着 3 步向导接入 AI。

### 方式 C：一体化打包

```bash
cd frontend && npm run build                # 产物写入 ../backend/static
cd ../backend && uvicorn qckit.main:app
# 前后端都在 http://localhost:8000
```

---

## 🤖 支持的 AI 平台

Web 界面已内置 6 家快速接入卡片 + 手把手指南：

| 平台 | 推荐场景 | 需要 |
|---|---|---|
| ☁️ **阿里百炼 (Qwen)** ⭐ | 国内首选，新用户额度多 | 支付宝/阿里云账号 |
| 🌋 **火山引擎 (豆包)** | 字节豆包 / DeepSeek / GLM 全家桶 | 手机号 + 实名 |
| 🐋 **DeepSeek** | 价格便宜，代码能力强 | 手机号 |
| 🌙 **Kimi (Moonshot)** | 128K 长上下文擅长 | 手机号 |
| 🌐 **OpenAI (GPT)** | 国际大厂 | 海外卡 + 代理 |
| 💻 **本地 vLLM / Ollama** | 私有部署 | 已跑起本地模型 |

配置支持三种方式（优先级从高到低）：
1. 环境变量 `QCKIT_LLM_BASE_URL` / `_API_KEY` / `_MODEL`（也认 `OPENAI_*`）
2. Web 界面「大模型 API」向导
3. `~/.qckit/config.yaml`

---

## 🎨 品牌主题

Web 界面「**配置 → 品牌主题**」支持：

- 🎨 **三通道调色**：画布拾色 + HEX 输入 + RGB (0-255) 输入
- 🏢 **企业信息**：公司名 / Logo → 自动落到 PPT/Excel 页眉
- 📐 **字体配置**：中英文字体分别指定
- 🎯 **6 套预设**：商务蓝 / 科技绿 / 品质红 / 稳重灰 / …

所有工具的导出物自动应用品牌主题，PPT 里都是可编辑的原生形状。

---

## 🧩 扩展一个 QC 工具

三步接入，见 [`docs/ADDING_A_TOOL.md`](docs/ADDING_A_TOOL.md)：

1. `backend/qckit/tools/<name>/service.py` — Prompt + Pydantic 模型 + `register()`
2. `backend/qckit/api/tools_api.py` — 加一条路由
3. `frontend/src/views/<Name>.vue` — 加页面 + 注册路由

---

## 🛠 技术栈

**后端**：Python 3.10+ · FastAPI · Pydantic v2 · OpenAI SDK · python-pptx · openpyxl  
**前端**：Vue 3 · Vite · Element Plus · Cytoscape · ECharts  
**部署**：Docker Compose · 支持 x86 / ARM

---

## 📄 License · 双许可

QCKit 采用 **双许可 (Dual License)** 模式：

- ✅ **非商业用途免费** — 个人学习、学术研究、非营利机构内部使用、开源集成、评估试用等，
  遵循 [PolyForm Noncommercial License 1.0.0](./LICENSE)
- 💼 **商业用途需授权** — 任何经营性目的（对外销售、SaaS、企业生产系统、
  付费咨询交付、闭源分发等）**必须**事先获得商业授权

**商业授权咨询**：请在本仓库 [提 Issue](https://github.com/yidingwanglnsy-boop/qckit/issues) 或 Discussion 联系版权持有人。

Copyright © 2026 王一定 (Yiding Wang)

---

## 🙏 致谢

- Element Plus / Cytoscape / ECharts / FastAPI 开源社区
- 所有为 QCKit 提供反馈的质量工程师们

如果 QCKit 帮到你，请点个 ⭐ Star，这是对开源作者最大的鼓励！
