# 新增一个 QC 工具

以「柏拉图（Pareto）」为例，走一遍完整流程。

## 1. 定义工具后端

`backend/qckit/tools/pareto/service.py`

```python
from pydantic import BaseModel
from ...core.llm import chat_json
from ...core.registry import ToolMeta, register


class ParetoRequest(BaseModel):
    topic: str
    items: list[dict]   # [{"name": "划痕", "count": 34}, ...]


class ParetoResponse(BaseModel):
    sorted_items: list[dict]     # 含累计占比
    vital_few: list[str]         # 关键少数（80%）
    insights: str
    recommendations: list[str]


SYSTEM = """你是 QC 顾问，擅长柏拉图分析（Pareto / 80-20 原则）。..."""


def analyze(req: ParetoRequest) -> ParetoResponse:
    data = chat_json(SYSTEM, req.model_dump_json())
    # 组装 & 校验
    return ParetoResponse(**data)


register(ToolMeta(
    key="pareto",
    name="柏拉图",
    category="QC七大手法",
    description="按频次/成本降序找出关键少数（vital few）",
    icon="TrendCharts",
))
```

`backend/qckit/tools/pareto/__init__.py`
```python
from .service import analyze, ParetoRequest, ParetoResponse
```

## 2. 注册路由 & 触发加载

`backend/qckit/tools/__init__.py`
```python
from . import relations, pareto  # noqa
```

`backend/qckit/api/tools_api.py`
```python
from ..tools.pareto import ParetoRequest, analyze as pareto_analyze

@router.post("/pareto/analyze")
def pareto_endpoint(req: ParetoRequest):
    return pareto_analyze(req)
```

## 3. 前端页面

- 在 `frontend/src/views/Pareto.vue` 创建输入 + ECharts 柱状+折线组合图。
- 在 `frontend/src/router.js` 加一条：
  `{ path: '/tools/pareto', component: () => import('./views/Pareto.vue') }`
- 在 `App.vue` 侧边栏菜单添加入口。

首页 `Home.vue` 会自动通过 `/api/tools` 拉取到新工具。

## 命名与角色约定

- `ToolMeta.key` 是 URL 和路由的唯一标识，用小写英文。
- `category` 建议使用："新QC七大手法" / "QC七大手法" / "问题分析" / "改善工具" 等。
- Prompt 必须要求 LLM 返回严格 JSON，并在后端做 schema 校验（Pydantic）。
- 所有面向用户的字段（说明、建议、判定依据）都用中文。
