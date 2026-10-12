from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from xsagent.core.dependencies import get_bible_service, get_patch_engine
from xsagent.core.exceptions import BibleSectionNotFoundError, FieldLockedError, ProjectNotFoundError
from xsagent.domain.memory.models import BibleLockUpdate, BibleSectionUpdate
from xsagent.domain.memory.patch_engine import PatchEngine
from xsagent.domain.memory.service import BibleService
from xsagent.jobs.models import PatchPreviewRequest

router = APIRouter(prefix="/api/projects/{project_id}/bible", tags=["bible"])


def _handle_errors(exc: Exception) -> HTTPException:
    if isinstance(exc, ProjectNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, BibleSectionNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, FieldLockedError):
        return HTTPException(status_code=409, detail=str(exc))
    raise exc


@router.get("/sections")
def list_bible_sections(
    project_id: str,
    service: Annotated[BibleService, Depends(get_bible_service)],
) -> list[str]:
    try:
        return service.list_sections(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{section}")
def get_bible_section(
    project_id: str,
    section: str,
    service: Annotated[BibleService, Depends(get_bible_service)],
) -> dict[str, Any]:
    try:
        return service.get_section(project_id, section)
    except (ProjectNotFoundError, BibleSectionNotFoundError) as exc:
        raise _handle_errors(exc) from exc


@router.put("/{section}")
def put_bible_section(
    project_id: str,
    section: str,
    body: BibleSectionUpdate,
    service: Annotated[BibleService, Depends(get_bible_service)],
) -> dict[str, Any]:
    try:
        return service.put_section(project_id, section, body.data)
    except (ProjectNotFoundError, BibleSectionNotFoundError, FieldLockedError) as exc:
        raise _handle_errors(exc) from exc


@router.patch("/{section}/locks")
def update_bible_locks(
    project_id: str,
    section: str,
    body: BibleLockUpdate,
    service: Annotated[BibleService, Depends(get_bible_service)],
) -> dict[str, Any]:
    try:
        return service.update_locked_fields(project_id, section, body.locked_fields)
    except (ProjectNotFoundError, BibleSectionNotFoundError) as exc:
        raise _handle_errors(exc) from exc


@router.post("/patch")
def bible_patch(
    project_id: str,
    body: PatchPreviewRequest,
    engine: Annotated[PatchEngine, Depends(get_patch_engine)],
) -> dict[str, Any]:
    if body.apply:
        result = engine.apply(project_id, body.patch)
        return {"mode": "apply", "result": result.model_dump()}
    previews = engine.preview(project_id, body.patch)
    return {"mode": "preview", "previews": [p.model_dump() for p in previews]}
