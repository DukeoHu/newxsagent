from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from xsagent.agents.explore import ExploreAgent
from xsagent.agents.prompts.defaults import DEFAULT_EXPLORE_PROMPT
from xsagent.core.dependencies import (
    get_action_log_service,
    get_explore_agent,
    get_outline_service,
    get_project_service,
    get_project_store,
    get_writing_context_builder,
)
from xsagent.core.exceptions import OutlineNotFoundError, ProjectNotFoundError
from xsagent.domain.action_log.service import ActionLogService
from xsagent.domain.explore.models import ExploreAdoptRequest, ExploreRecord
from xsagent.domain.outline.service import OutlineService
from xsagent.domain.project.service import ProjectService
from xsagent.storage.project_store import ProjectStore
from xsagent.agents.context import WritingContextBuilder

router = APIRouter(prefix="/api/projects/{project_id}", tags=["explore"])


class ExploreRequest(BaseModel):
    chapter_id: str | None = Field(default=None, pattern=r"^ch_\d{3,}$")
    prompt: str = DEFAULT_EXPLORE_PROMPT
    count: int = Field(default=3, ge=1, le=5)


def _pick_chapter_id(outlines: OutlineService, project_id: str, chapter_id: str | None) -> str:
    if chapter_id:
        return chapter_id
    chapters = outlines.list_chapter_blueprints(project_id)
    if not chapters:
        return "ch_001"
    pending = [x for x in chapters if x.status == "pending"]
    if pending:
        return pending[0].chapter_id
    return chapters[-1].chapter_id


@router.post("/explore", response_model=ExploreRecord)
async def create_explore(
    project_id: str,
    body: ExploreRequest,
    outlines: Annotated[OutlineService, Depends(get_outline_service)],
    store: Annotated[ProjectStore, Depends(get_project_store)],
    logs: Annotated[ActionLogService, Depends(get_action_log_service)],
    projects: Annotated[ProjectService, Depends(get_project_service)],
    context_builder: Annotated[WritingContextBuilder, Depends(get_writing_context_builder)],
    explore: Annotated[ExploreAgent, Depends(get_explore_agent)],
) -> ExploreRecord:
    try:
        chapter_id = _pick_chapter_id(outlines, project_id, body.chapter_id)
        project = projects.get_project(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    ctx = context_builder.build(project, chapter_id, body.prompt)
    options = await explore.propose(
        chapter_id=chapter_id,
        prompt=body.prompt,
        count=body.count,
        context=ctx,
    )
    recommended, reason = await explore.judge(options, context=ctx)
    record = ExploreRecord(
        explore_id=uuid4().hex[:12],
        project_id=project_id,
        chapter_id=chapter_id,
        prompt=body.prompt,
        created_at=datetime.now(UTC).isoformat(),
        options=options,
        recommended_option_id=recommended or None,
        judge_reason=reason,
    )
    path = store.project_path(project_id) / "explore" / f"{record.explore_id}.json"
    store.write_json(path, record.model_dump())
    logs.append(
        project_id,
        action_type="explore.create",
        diff_summary=f"创建探索任务 {record.explore_id}（{chapter_id}）",
        metadata={
            "explore_id": record.explore_id,
            "chapter_id": chapter_id,
            "recommended_option_id": record.recommended_option_id,
        },
    )
    return record


@router.post("/explore/{explore_id}/adopt")
def adopt_explore_option(
    project_id: str,
    explore_id: str,
    body: ExploreAdoptRequest,
    outlines: Annotated[OutlineService, Depends(get_outline_service)],
    store: Annotated[ProjectStore, Depends(get_project_store)],
    logs: Annotated[ActionLogService, Depends(get_action_log_service)],
) -> dict:
    path = store.project_path(project_id) / "explore" / f"{explore_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Explore record not found: {explore_id}")

    record = ExploreRecord.model_validate(store.read_json(path))
    option = next((x for x in record.options if x.option_id == body.option_id), None)
    if option is None:
        raise HTTPException(status_code=404, detail=f"Explore option not found: {body.option_id}")

    try:
        updated = outlines.put_chapter_blueprint(
            project_id,
            option.chapter_id,
            {
                "title": option.title,
                "beats": option.beats,
                "constraints": option.constraints,
                "status": "ready",
            },
        )
    except (ProjectNotFoundError, OutlineNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    logs.append(
        project_id,
        action_type="explore.adopt",
        diff_summary=f"采纳探索方案 {body.option_id} 到 {option.chapter_id}",
        metadata={
            "explore_id": explore_id,
            "option_id": body.option_id,
            "actor": body.actor,
            "chapter_id": option.chapter_id,
        },
    )
    return {"ok": True, "chapter_blueprint": updated.model_dump()}
