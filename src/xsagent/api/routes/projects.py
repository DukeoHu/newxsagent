from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from xsagent.core.dependencies import get_project_service
from xsagent.core.exceptions import ProjectNotFoundError
from xsagent.domain.project.models import (
    Project,
    ProjectCreate,
    ProjectStatus,
    ProjectUpdate,
)
from xsagent.domain.project.service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[Project])
def list_projects(
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[Project]:
    return service.list_projects()


@router.post("", response_model=Project, status_code=201)
def create_project(
    project_in: ProjectCreate,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> Project:
    return service.create(project_in)


@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: str,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> Project:
    try:
        return service.get_project(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> Project:
    try:
        return service.update(project_id, project_in)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: str,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> Response:
    try:
        service.delete(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)


@router.get("/{project_id}/status", response_model=ProjectStatus)
def get_project_status(
    project_id: str,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectStatus:
    try:
        return service.get_status(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
