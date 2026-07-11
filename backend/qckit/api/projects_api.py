"""QCC 项目 API."""
from __future__ import annotations

from urllib.parse import quote
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..projects import (Project, STAGES, STAGE_LABELS, TOOL_DEFAULT_STAGE,
                        Attachment)
from ..core.project_pptx import build_project_pptx

router = APIRouter(prefix="/api/projects", tags=["projects"])


class CreateProjectIn(BaseModel):
    name: str
    circle: str = ""
    leader: str = ""
    members: list[str] = []
    topic: str = ""


class UpdateProjectIn(BaseModel):
    name: str | None = None
    circle: str | None = None
    leader: str | None = None
    members: list[str] | None = None
    topic: str | None = None


class AttachIn(BaseModel):
    tool: str
    snapshot: dict
    result: dict
    stage: str | None = None
    title: str = ""


@router.get("/meta")
def meta():
    return {
        "stages": STAGES,
        "stage_labels": STAGE_LABELS,
        "tool_default_stage": TOOL_DEFAULT_STAGE,
    }


@router.get("")
def list_projects() -> list[dict]:
    return [p.model_dump() for p in Project.all()]


@router.post("")
def create_project(body: CreateProjectIn) -> dict:
    p = Project(**body.model_dump())
    p.save()
    return p.model_dump()


@router.get("/{pid}")
def get_project(pid: str) -> dict:
    p = Project.load(pid)
    if not p:
        raise HTTPException(404, "项目不存在")
    return p.model_dump()


@router.patch("/{pid}")
def update_project(pid: str, body: UpdateProjectIn) -> dict:
    p = Project.load(pid)
    if not p:
        raise HTTPException(404, "项目不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    p.save()
    return p.model_dump()


@router.delete("/{pid}")
def delete_project(pid: str) -> dict:
    p = Project.load(pid)
    if not p:
        raise HTTPException(404, "项目不存在")
    p.delete()
    return {"ok": True}


@router.post("/{pid}/attach")
def attach(pid: str, body: AttachIn) -> dict:
    p = Project.load(pid)
    if not p:
        raise HTTPException(404, "项目不存在")
    att = p.attach(body.tool, body.snapshot, body.result,
                    stage=body.stage, title=body.title)
    return att.model_dump()


@router.delete("/{pid}/stages/{stage}/{aid}")
def detach(pid: str, stage: str, aid: str) -> dict:
    p = Project.load(pid)
    if not p:
        raise HTTPException(404, "项目不存在")
    if not p.detach(stage, aid):
        raise HTTPException(404, "附件不存在")
    return {"ok": True}


@router.get("/{pid}/export/pptx")
def export_project_pptx(pid: str) -> StreamingResponse:
    """一键合成整个项目的完整 QC-STORY 报告 PPTX."""
    p = Project.load(pid)
    if not p:
        raise HTTPException(404, "项目不存在")
    buf = build_project_pptx(p.model_dump())
    filename = f"QCC项目_{p.name}.pptx"
    quoted = quote(filename)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quoted}"},
    )
