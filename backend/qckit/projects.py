"""QCC 项目容器 —— 本地文件存储 (~/.qckit/projects/*.yaml).

一个 QCC 项目 = 一个圈 + 一个主题, 挂靠各阶段的分析产物。
阶段来自 QC-STORY 十步法:
  select    选题
  current   现状调查
  target    目标设定
  cause     要因分析
  root      根因确认
  measure   对策制定
  schedule  实施排期
  execute   实施记录
  evaluate  效果确认
  standard  标准化
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

PROJECTS_DIR = Path.home() / ".qckit" / "projects"
STAGES = ["select", "current", "target", "cause", "root",
          "measure", "schedule", "execute", "evaluate", "standard"]
STAGE_LABELS = {
    "select": "选题", "current": "现状调查", "target": "目标设定",
    "cause": "要因分析", "root": "根因确认", "measure": "对策制定",
    "schedule": "实施排期", "execute": "实施记录",
    "evaluate": "效果确认", "standard": "标准化",
}
# 工具默认落到哪个阶段 (用户可覆盖)
TOOL_DEFAULT_STAGE = {
    "qcc_guide": "select", "relations": "current", "affinity": "current",
    "pareto": "current",   "fishbone": "cause",   "tree": "measure",
    "matrix": "measure",   "mda": "measure",      "w5h2": "measure",
    "rca": "root",         "pdpc": "schedule",    "arrow": "schedule",
    "radar": "evaluate",
}


class Attachment(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    tool: str                                # 工具 key
    title: str = ""                          # 挂靠时的显示名 (默认取 topic)
    snapshot: dict = Field(default_factory=dict)     # 输入表单快照
    result: dict = Field(default_factory=dict)       # 分析结果
    at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class Project(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    circle: str = ""                # 圈名
    leader: str = ""                # 圈长
    members: list[str] = []
    topic: str = ""                 # 项目主题
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    stages: dict[str, list[Attachment]] = Field(
        default_factory=lambda: {s: [] for s in STAGES})

    # ── I/O ───────────────────────────────────────────
    @property
    def slug(self) -> str:
        base = re.sub(r"[^\w\u4e00-\u9fa5-]+", "_", self.name).strip("_") or self.id
        return f"{base}_{self.id[:6]}"

    @property
    def path(self) -> Path:
        return PROJECTS_DIR / f"{self.slug}.yaml"

    def save(self) -> None:
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.updated_at = datetime.now().isoformat(timespec="seconds")
        # 保证所有阶段都存在
        for s in STAGES:
            self.stages.setdefault(s, [])
        self.path.write_text(
            yaml.safe_dump(self.model_dump(), allow_unicode=True, sort_keys=False),
            encoding="utf-8")
        self.path.chmod(0o600)

    @classmethod
    def load(cls, project_id: str) -> "Project | None":
        for p in PROJECTS_DIR.glob("*.yaml"):
            try:
                data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                if data.get("id") == project_id:
                    return cls(**data)
            except (yaml.YAMLError, TypeError, ValueError):
                continue
        return None

    @classmethod
    def all(cls) -> list["Project"]:
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        out = []
        for p in sorted(PROJECTS_DIR.glob("*.yaml"),
                         key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                out.append(cls(**data))
            except (yaml.YAMLError, TypeError, ValueError):
                continue
        return out

    def delete(self) -> bool:
        if self.path.exists():
            self.path.unlink()
            return True
        return False

    # ── 挂靠 ───────────────────────────────────────────
    def attach(self, tool: str, snapshot: dict, result: dict,
               stage: str | None = None, title: str = "") -> Attachment:
        stage = stage or TOOL_DEFAULT_STAGE.get(tool, "current")
        if stage not in STAGES:
            raise ValueError(f"未知阶段: {stage}")
        att = Attachment(
            tool=tool,
            title=title or snapshot.get("topic") or snapshot.get("problem") or tool,
            snapshot=snapshot,
            result=result,
        )
        self.stages.setdefault(stage, []).append(att)
        self.save()
        return att

    def detach(self, stage: str, attachment_id: str) -> bool:
        items = self.stages.get(stage, [])
        before = len(items)
        self.stages[stage] = [a for a in items if a.id != attachment_id]
        if len(self.stages[stage]) < before:
            self.save()
            return True
        return False
