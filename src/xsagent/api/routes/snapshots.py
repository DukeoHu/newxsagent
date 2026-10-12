from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from xsagent.core.dependencies import get_action_log_service, get_llm_log_service, get_snapshot_service
from xsagent.core.exceptions import ProjectNotFoundError, SnapshotNotFoundError
from xsagent.domain.action_log.models import ActionLogEntry, SnapshotInfo
from xsagent.domain.action_log.service import ActionLogService
from xsagent.domain.llm_log.models import LLMLogEntry
from xsagent.domain.llm_log.service import LLMLogService
from xsagent.storage.snapshot_service import SnapshotService

router = APIRouter(prefix="/api/projects/{project_id}", tags=["snapshots", "logs"])


class SnapshotCreate(BaseModel):
    label: str | None = None


@router.get("/snapshots", response_model=list[SnapshotInfo])
def list_snapshots(
    project_id: str,
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
) -> list[SnapshotInfo]:
    try:
        return service.list_snapshots(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/snapshots", response_model=SnapshotInfo, status_code=201)
def create_snapshot(
    project_id: str,
    body: SnapshotCreate,
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
) -> SnapshotInfo:
    try:
        return service.create(project_id, label=body.label)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/snapshots/{snapshot_id}/rollback", response_model=SnapshotInfo)
def rollback_snapshot(
    project_id: str,
    snapshot_id: str,
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
) -> SnapshotInfo:
    try:
        return service.rollback(project_id, snapshot_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SnapshotNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/logs/actions", response_model=list[ActionLogEntry])
def list_action_logs(
    project_id: str,
    service: Annotated[ActionLogService, Depends(get_action_log_service)],
    limit: int = 50,
) -> list[ActionLogEntry]:
    return service.list_entries(project_id, limit=limit)


@router.get("/logs/llm", response_model=list[LLMLogEntry])
def list_llm_logs(
    project_id: str,
    service: Annotated[LLMLogService, Depends(get_llm_log_service)],
    limit: int = 50,
) -> list[LLMLogEntry]:
    return service.list_entries(project_id, limit=limit)
