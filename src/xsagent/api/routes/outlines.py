from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from xsagent.core.dependencies import get_outline_planning_service, get_outline_service
from xsagent.core.exceptions import OutlineNotFoundError, ProjectNotFoundError
from xsagent.domain.outline.models import ChapterBlueprint, OutlineBundle, VolumeOutline
from xsagent.domain.outline.planning_service import OutlinePlanningService
from xsagent.domain.outline.service import OutlineService

router = APIRouter(prefix="/api/projects/{project_id}/outlines", tags=["outlines"])


class OutlineGenerateRequest(BaseModel):
    scope: Literal["all", "volume", "chapters"] = "chapters"
    volume_id: str | None = None
    chapter_ids: list[str] = Field(default_factory=list)
    only_pending: bool = True
    apply: bool = True
    regenerate_master: bool = False


@router.post("/generate-master")
async def generate_master_outline(
    project_id: str,
    planning: Annotated[OutlinePlanningService, Depends(get_outline_planning_service)],
) -> dict[str, Any]:
    try:
        return await planning.generate_master(project_id, apply=True)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


class GenerateThreadsRequest(BaseModel):
    only_missing: bool = True
    apply: bool = True


@router.post("/generate-threads")
async def generate_narrative_threads(
    project_id: str,
    body: GenerateThreadsRequest,
    planning: Annotated[OutlinePlanningService, Depends(get_outline_planning_service)],
) -> dict[str, Any]:
    """AI 自动为各卷生成 / 补全叙事线程（无需手填）。"""
    try:
        return await planning.generate_threads(
            project_id,
            only_missing=body.only_missing,
            apply=body.apply,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OutlineNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/generate")
async def generate_outlines(
    project_id: str,
    body: OutlineGenerateRequest,
    planning: Annotated[OutlinePlanningService, Depends(get_outline_planning_service)],
) -> dict[str, Any]:
    try:
        if body.scope == "all":
            return await planning.generate_all(
                project_id,
                only_pending=body.only_pending,
                apply=body.apply,
                regenerate_master=body.regenerate_master,
            )
        if body.scope == "volume":
            if not body.volume_id:
                raise HTTPException(status_code=400, detail="volume_id is required")
            return await planning.generate_volume(
                project_id,
                body.volume_id,
                only_pending=body.only_pending,
                apply=body.apply,
            )
        if not body.chapter_ids:
            raise HTTPException(status_code=400, detail="chapter_ids is required")
        return await planning.generate_chapters(
            project_id,
            body.chapter_ids,
            apply=body.apply,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OutlineNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/chapters/{chapter_id}/generate")
async def generate_chapter_blueprint(
    project_id: str,
    chapter_id: str,
    planning: Annotated[OutlinePlanningService, Depends(get_outline_planning_service)],
) -> dict[str, Any]:
    try:
        return await planning.recommend_chapter(project_id, chapter_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=OutlineBundle)
def get_outlines(
    project_id: str,
    service: Annotated[OutlineService, Depends(get_outline_service)],
) -> OutlineBundle:
    try:
        return service.get_bundle(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/master")
def get_master_outline(
    project_id: str,
    service: Annotated[OutlineService, Depends(get_outline_service)],
) -> dict[str, Any]:
    try:
        return service.get_master(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/master")
def put_master_outline(
    project_id: str,
    body: dict[str, Any],
    service: Annotated[OutlineService, Depends(get_outline_service)],
) -> dict[str, Any]:
    try:
        return service.put_master(project_id, body)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/volumes", response_model=list[VolumeOutline])
def list_volumes(
    project_id: str,
    service: Annotated[OutlineService, Depends(get_outline_service)],
) -> list[VolumeOutline]:
    try:
        return service.list_volumes(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/volumes/{volume_id}", response_model=VolumeOutline)
def get_volume(
    project_id: str,
    volume_id: str,
    service: Annotated[OutlineService, Depends(get_outline_service)],
) -> VolumeOutline:
    try:
        return service.get_volume(project_id, volume_id)
    except (ProjectNotFoundError, OutlineNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/volumes/{volume_id}", response_model=VolumeOutline)
def put_volume(
    project_id: str,
    volume_id: str,
    body: dict[str, Any],
    service: Annotated[OutlineService, Depends(get_outline_service)],
) -> VolumeOutline:
    try:
        return service.put_volume(project_id, volume_id, body)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/chapters", response_model=list[ChapterBlueprint])
def list_chapter_blueprints(
    project_id: str,
    service: Annotated[OutlineService, Depends(get_outline_service)],
) -> list[ChapterBlueprint]:
    try:
        return service.list_chapter_blueprints(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/chapters/{chapter_id}", response_model=ChapterBlueprint)
def get_chapter_blueprint(
    project_id: str,
    chapter_id: str,
    service: Annotated[OutlineService, Depends(get_outline_service)],
) -> ChapterBlueprint:
    try:
        return service.get_chapter_blueprint(project_id, chapter_id)
    except (ProjectNotFoundError, OutlineNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/chapters/{chapter_id}", response_model=ChapterBlueprint)
def put_chapter_blueprint(
    project_id: str,
    chapter_id: str,
    body: dict[str, Any],
    service: Annotated[OutlineService, Depends(get_outline_service)],
) -> ChapterBlueprint:
    try:
        return service.put_chapter_blueprint(project_id, chapter_id, body)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
