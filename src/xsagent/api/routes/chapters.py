from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from xsagent.core.dependencies import get_chapter_service
from xsagent.core.exceptions import (
    ChapterAlreadyExistsError,
    ChapterNotFoundError,
    ProjectNotFoundError,
)
from xsagent.domain.writing.models import Chapter, ChapterCreate, ChapterSummary, ChapterUpdate
from xsagent.domain.writing.service import ChapterService

router = APIRouter(prefix="/api/projects/{project_id}/chapters", tags=["chapters"])


@router.get("", response_model=list[ChapterSummary])
def list_chapters(
    project_id: str,
    service: Annotated[ChapterService, Depends(get_chapter_service)],
) -> list[ChapterSummary]:
    try:
        return service.list_chapters(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("", response_model=Chapter, status_code=201)
def create_chapter(
    project_id: str,
    body: ChapterCreate,
    service: Annotated[ChapterService, Depends(get_chapter_service)],
) -> Chapter:
    try:
        return service.create_chapter(project_id, body)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ChapterAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{chapter_id}", response_model=Chapter)
def get_chapter(
    project_id: str,
    chapter_id: str,
    service: Annotated[ChapterService, Depends(get_chapter_service)],
) -> Chapter:
    try:
        return service.get_chapter(project_id, chapter_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ChapterNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{chapter_id}", response_model=Chapter)
def update_chapter(
    project_id: str,
    chapter_id: str,
    body: ChapterUpdate,
    service: Annotated[ChapterService, Depends(get_chapter_service)],
) -> Chapter:
    try:
        return service.update_chapter(project_id, chapter_id, body)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ChapterNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{chapter_id}", status_code=204)
def delete_chapter(
    project_id: str,
    chapter_id: str,
    service: Annotated[ChapterService, Depends(get_chapter_service)],
) -> Response:
    try:
        service.delete_chapter(project_id, chapter_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ChapterNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)
