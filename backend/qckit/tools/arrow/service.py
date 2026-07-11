"""箭线图法 (Arrow Diagram / CPM 关键路径) —— 任务排期 + 识别关键路径。

后端做:
  1. LLM 从任务描述推断前置依赖 + PERT 三点估算
  2. Python 计算 ES/EF/LS/LF/浮时 + 关键路径
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register


class TaskIn(BaseModel):
    name: str
    duration: float | None = None      # 天; 若空由 LLM 估
    predecessors: list[str] | None = None
    description: str | None = None
    owner: str | None = None


class ArrowRequest(BaseModel):
    topic: str = Field(..., description="项目主题")
    tasks: list[TaskIn] = Field(..., min_length=2)
    context: str | None = None
    auto_infer: bool = Field(True, description="LLM 自动推断依赖/工期")


class TaskOut(BaseModel):
    name: str
    duration: float
    predecessors: list[str] = []
    owner: str = ""
    es: float = 0    # earliest start
    ef: float = 0
    ls: float = 0
    lf: float = 0
    slack: float = 0
    is_critical: bool = False


class ArrowResponse(BaseModel):
    topic: str
    tasks: list[TaskOut]
    critical_path: list[str] = []
    project_duration: float = 0
    resource_conflicts: list[dict] = []
    summary: str = ""
    recommendations: list[str] = []


SYSTEM_PROMPT = """你是 QC 新七大手法「箭线图法 / 关键路径 CPM」专家。
用户给了任务清单, 请:
1. 若某任务没有工期, 用 PERT 估算: t = (O + 4M + P) / 6 (O 乐观, M 最可能, P 悲观), 单位=天
2. 若某任务没有前置, 从任务描述推断依赖 (如 "焊接" 必然依赖 "备料")
3. 检测同一 owner 在时间上冲突的任务

严格 JSON:
{
  "tasks":[
    {"name":"...","duration":3.5,"predecessors":["A","B"],"owner":"技术员1",
     "reason":"依赖 A 因为 xxx; 工期基于 PERT(2,3,5)"}
  ],
  "resource_conflicts":[{"owner":"...","tasks":["A","B"],"advice":"..."}],
  "summary":"...","recommendations":["..."]
}
"""


def _cpm(tasks: list[TaskOut]) -> tuple[list[str], float]:
    """标准 CPM: 前向传播 ES/EF, 后向传播 LS/LF, 浮时 = LS-ES。"""
    idx = {t.name: t for t in tasks}
    # 检测已存在的名字
    for t in tasks:
        t.predecessors = [p for p in t.predecessors if p in idx]

    # 前向: 拓扑序 (Kahn)
    order = []
    remaining = {t.name: set(t.predecessors) for t in tasks}
    ready = [n for n, deps in remaining.items() if not deps]
    while ready:
        n = ready.pop(0)
        order.append(n)
        for m, deps in remaining.items():
            if n in deps:
                deps.discard(n)
                if not deps and m not in order and m not in ready:
                    ready.append(m)
    # 循环依赖直接返回空
    if len(order) < len(tasks):
        return [], 0

    for name in order:
        t = idx[name]
        t.es = max((idx[p].ef for p in t.predecessors), default=0.0)
        t.ef = t.es + t.duration

    project_dur = max(t.ef for t in tasks)

    # 后向
    for t in tasks:
        t.lf = project_dur
    for name in reversed(order):
        t = idx[name]
        successors = [x for x in tasks if name in x.predecessors]
        if successors:
            t.lf = min(s.ls for s in successors)
        t.ls = t.lf - t.duration
        t.slack = round(t.ls - t.es, 3)
        t.is_critical = abs(t.slack) < 1e-6

    critical = [n for n in order if idx[n].is_critical]
    return critical, project_dur


def analyze(req: ArrowRequest) -> ArrowResponse:
    # 先看是否需要 LLM 补全
    need_llm = req.auto_infer and any(
        t.duration is None or t.predecessors is None for t in req.tasks)

    llm_data: dict = {}
    if need_llm:
        ctx = f"\n背景: {req.context}" if req.context else ""
        task_desc = "\n".join(
            f"- {t.name}"
            + (f" [工期={t.duration}d]" if t.duration else "")
            + (f" [前置={','.join(t.predecessors)}]" if t.predecessors else "")
            + (f" [owner={t.owner}]" if t.owner else "")
            + (f": {t.description}" if t.description else "")
            for t in req.tasks
        )
        user = f"项目: {req.topic}{ctx}\n任务清单:\n{task_desc}"
        llm_data = chat_json(SYSTEM_PROMPT, user)

    llm_by_name = {t.get("name"): t for t in llm_data.get("tasks", [])}

    tasks_out: list[TaskOut] = []
    for t in req.tasks:
        info = llm_by_name.get(t.name, {})
        dur = t.duration if t.duration is not None else float(info.get("duration", 1) or 1)
        preds = t.predecessors if t.predecessors is not None else list(info.get("predecessors", []))
        tasks_out.append(TaskOut(
            name=t.name,
            duration=max(0.1, float(dur)),
            predecessors=preds,
            owner=t.owner or info.get("owner", "") or "",
        ))

    critical, project_dur = _cpm(tasks_out)

    return ArrowResponse(
        topic=req.topic,
        tasks=tasks_out,
        critical_path=critical,
        project_duration=round(project_dur, 2),
        resource_conflicts=list(llm_data.get("resource_conflicts", []))[:20],
        summary=llm_data.get("summary", ""),
        recommendations=list(llm_data.get("recommendations", []))[:8],
    )


register(ToolMeta(
    key="arrow",
    name="箭线图",
    category="新QC七大手法",
    description="任务网络图 + 关键路径 CPM, LLM 推断依赖 + PERT 工期估算。",
    icon="Right",
))
