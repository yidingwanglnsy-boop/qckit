"""QCC 思路生成器 —— 问题解决型 QCC 五阶段流程指引。

输入: 课题(可选)、行业(可选)、经验级别、期望产出
输出: 五个阶段, 每段含目标/关键动作/推荐工具/建议/陷阱
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ...core.llm import chat_json
from ...core.registry import ToolMeta, register

STAGES = [
    ("select",  "选择课题 · 把握现状"),
    ("analyze", "分析根因"),
    ("plan",    "拟定对策"),
    ("execute", "对策实施 · 效果确认"),
    ("summary", "总结 · 标准化 · 反思"),
]

# qckit 内置工具 key -> 前端路由
TOOL_ROUTES = {
    "pareto":    "/tools/pareto",
    "relations": "/tools/relations",
    "affinity":  "/tools/affinity",
    "radar":     "/tools/radar",
    "w5h2":      "/tools/w5h2",
    "rca":       "/tools/rca",
    "fishbone":  "/tools/fishbone",
}


class ToolRef(BaseModel):
    key:  str = ""            # qckit 工具 key, 无匹配则空串
    name: str                  # 显示名, 如 "柏拉图 (Pareto)"
    why:  str                  # 为何用它, 一句话
    route: str = ""            # 前端路由


class Stage(BaseModel):
    id:       str
    title:    str
    goal:     str
    actions:  list[str] = Field(default_factory=list)  # 关键动作
    tools:    list[ToolRef] = Field(default_factory=list)
    tips:     list[str] = Field(default_factory=list)
    pitfalls: list[str] = Field(default_factory=list)


class GuideRequest(BaseModel):
    topic:      str = ""
    industry:   str = ""
    experience: Literal["新手", "熟悉", "资深"] = "新手"
    focus:      str = ""       # 用户额外偏好, 如 "重点讲根因分析"


class GuideResponse(BaseModel):
    topic:     str
    stages:    list[Stage]
    overview:  str = ""        # 整体思路一句话


SYSTEM = """你是精通 QCC(品管圈)方法论的资深顾问, 面向制造业 QCC 圈员。
请根据用户课题输出 "问题解决型 QCC" 的五阶段思路指引:
  1. select  - 选择课题 · 把握现状
  2. analyze - 分析根因
  3. plan    - 拟定对策
  4. execute - 对策实施 · 效果确认
  5. summary - 总结 · 标准化 · 反思

每个阶段严格返回:
  goal      : 本阶段目标, 1-2 句
  actions   : 关键动作 3-5 条, 每条动词开头, 20 字内
  tools     : 推荐质量工具 2-4 个, 每个含
                key  ("pareto"/"relations"/"affinity"/"radar"/"w5h2"/"rca"/"fishbone" 之一,
                       若为通用工具如"查检表"/"直方图"/"甘特图"则填空串 "")
                name ("柏拉图 (Pareto)" 这种中英组合)
                why  (为何用它, 1 句 30 字内)
  tips      : 使用建议 2-3 条, 结合用户 experience={experience} 给出难度适配
  pitfalls  : 常见陷阱 2-3 条

整体 overview: 一句 60 字内的思路总述。

用户经验级别={experience}, 语气按此匹配:
- "新手": 每步解释更细, 少术语, 多举例
- "熟悉": 简明, 突出选择判据
- "资深": 精炼, 只讲要点与常犯错误

严格 JSON:
{{
  "overview": "...",
  "stages": {{
    "select":  {{"goal":"","actions":[],"tools":[{{"key":"","name":"","why":""}}],"tips":[],"pitfalls":[]}},
    "analyze": {{...}},
    "plan":    {{...}},
    "execute": {{...}},
    "summary": {{...}}
  }}
}}"""


def analyze(req: GuideRequest) -> GuideResponse:
    lines = [
        f"课题: {req.topic or '（未指定，请给通用示例）'}",
        f"行业: {req.industry or '（未指定）'}",
        f"经验级别: {req.experience}",
    ]
    if req.focus:
        lines.append(f"额外偏好: {req.focus}")
    user = "\n".join(lines)

    try:
        data = chat_json(SYSTEM.format(experience=req.experience), user)
    except Exception as e:
        return _fallback(req, f"LLM 不可用: {e}")

    stages_raw = data.get("stages") or {}
    stages: list[Stage] = []
    for sid, title in STAGES:
        s = stages_raw.get(sid) or {}
        tools = []
        for t in (s.get("tools") or []):
            if not isinstance(t, dict):
                continue
            key = str(t.get("key", "")).strip()
            tools.append(ToolRef(
                key=key,
                name=str(t.get("name", "")).strip(),
                why=str(t.get("why", "")).strip(),
                route=TOOL_ROUTES.get(key, ""),
            ))
        stages.append(Stage(
            id=sid, title=title,
            goal=str(s.get("goal", "")).strip(),
            actions=[str(x).strip() for x in (s.get("actions") or []) if str(x).strip()],
            tools=tools,
            tips=[str(x).strip() for x in (s.get("tips") or []) if str(x).strip()],
            pitfalls=[str(x).strip() for x in (s.get("pitfalls") or []) if str(x).strip()],
        ))

    return GuideResponse(
        topic=req.topic or "（通用）",
        stages=stages,
        overview=str(data.get("overview", "")).strip(),
    )


def _fallback(req: GuideRequest, note: str) -> GuideResponse:
    """LLM 挂了时的通用骨架，保证前端可用。"""
    T = lambda k, n, w: ToolRef(key=k, name=n, why=w, route=TOOL_ROUTES.get(k, ""))
    stages = [
        Stage(id="select", title="选择课题 · 把握现状",
              goal="从多个候选课题中选一个高价值课题，用数据勾画现状。",
              actions=["列候选课题 5-8 个", "按 4 评价维度打分", "收集 4 周基线数据", "定义衡量指标(不良率/工时/成本)"],
              tools=[T("radar","雷达图 (Radar)","多维评估候选课题优先级"),
                     T("pareto","柏拉图 (Pareto)","锁定关键少数问题"),
                     T("", "查检表 (Check Sheet)","现状数据采集")],
              tips=["选'半年内可见效'的课题","目标数字化：如不良率 3.5%→1.5%"],
              pitfalls=["课题过大做不动","只凭经验不上数据"]),
        Stage(id="analyze", title="分析根因",
              goal="从症状回溯到末端可动根因，避免只治标。",
              actions=["列出所有可能原因","4M 分类归纳","三现主义现场验证","筛选要因(是否要因)"],
              tools=[T("fishbone","鱼骨图 (4M)","系统列出人机料法各类原因"),
                     T("relations","关联图 (Relations)","梳理复杂因果链"),
                     T("rca","根因确认 (RCA)","逐一验证末端要因")],
              tips=["末端原因必须可执行","三现验证：现场/现物/现实"],
              pitfalls=["把现象当原因","主观判断跳过验证"]),
        Stage(id="plan", title="拟定对策",
              goal="对每条要因产出可执行、可评价的对策。",
              actions=["对策头脑风暴","5W2H 展开","可行性/成本/效果评价","做甘特图排期"],
              tools=[T("w5h2","5W2H (Why/What/…)","把对策落到人事时地方法度"),
                     T("affinity","亲和图 (Affinity)","归纳发散的对策想法"),
                     T("","矩阵评价 (Matrix)","多维打分选优")],
              tips=["每条对策指定 Owner + Due","短平快对策先做"],
              pitfalls=["对策泛化 - 无 Owner","对策≠要因（错配）"]),
        Stage(id="execute", title="对策实施 · 效果确认",
              goal="按 PDCA 推进对策，验证效果达标。",
              actions=["按甘特图周会跟踪","收集实施后数据","前后对比","评估目标达成率"],
              tools=[T("pareto","柏拉图 (前后对比)","看关键问题占比下降"),
                     T("","控制图 (SPC)","确认过程稳定"),
                     T("","查检表","实施数据记录")],
              tips=["实施期 4-8 周为宜","效果不达标返 analyze 阶段"],
              pitfalls=["只看主指标忽略副作用","数据取样不足"]),
        Stage(id="summary", title="总结 · 标准化 · 反思",
              goal="固化成果转标准，圈组反思学习。",
              actions=["修订/新建作业标准","分享横展至类似产线","无形成果盘点","下一课题预告"],
              tools=[T("","作业指导书 (SOP)","把有效对策沉淀为标准"),
                     T("","雷达图 (Radar)","评估圈能力提升"),
                     T("","一页 A3 报告","汇报可视化")],
              tips=["有形成果+无形成果都要盘","做一页 A3 便于横展"],
              pitfalls=["做完就散没有标准化","过度包装数据"]),
    ]
    return GuideResponse(
        topic=req.topic or "（通用）",
        stages=stages,
        overview=f"问题解决型 QCC 五阶段: 选题定现状 → 分析找要因 → 拟定对策 → 实施验证 → 标准化。({note})",
    )


register(ToolMeta(
    key="qcc_guide",
    name="QCC 思路生成器",
    category="通用",
    description="面向新手的问题解决型 QCC 五阶段思路：每阶段的目标、动作、推荐工具、建议、陷阱。",
    icon="Guide",
))
