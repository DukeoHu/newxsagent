from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from xsagent.agents.maintenance import DistillAgent, DistillReport, DreamAgent
from xsagent.core.dependencies import (
    get_action_log_service,
    get_distill_agent,
    get_dream_agent,
    get_pending_service,
)
from xsagent.core.exceptions import ProjectNotFoundError
from xsagent.domain.action_log.service import ActionLogService
from xsagent.domain.memory.dream import DreamReport
from xsagent.domain.quality.models import PendingItemStatus
from xsagent.domain.quality.pending_service import PendingService

router = APIRouter(prefix="/api/projects/{project_id}/maintenance", tags=["maintenance"])


@router.post("/dream", response_model=DreamReport)
async def run_dream(
    project_id: str,
    agent: Annotated[DreamAgent, Depends(get_dream_agent)],
    logs: Annotated[ActionLogService, Depends(get_action_log_service)],
) -> DreamReport:
    try:
        report = await agent.run(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    logs.append(
        project_id,
        action_type="memory.dream",
        diff_summary="已整理项目记忆（去重、清理失效引用）",
        metadata=report.model_dump(),
    )
    return report


@router.post("/distill", response_model=DistillReport)
async def run_distill(
    project_id: str,
    agent: Annotated[DistillAgent, Depends(get_distill_agent)],
    pending: Annotated[PendingService, Depends(get_pending_service)],
    logs: Annotated[ActionLogService, Depends(get_action_log_service)],
) -> DistillReport:
    try:
        decisions = [
            f"{item.item_type}/{item.status.value}: {item.summary}"
            for item in pending.list_all(project_id)
            if item.status in {PendingItemStatus.RESOLVED, PendingItemStatus.IGNORED}
        ]
        if not decisions:
            decisions = [
                f"{entry.action_type}: {entry.diff_summary}"
                for entry in logs.list_entries(project_id, limit=30)
                if entry.action_type.startswith("supervision.")
            ]
        report = await agent.run(project_id, decisions)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    logs.append(
        project_id,
        action_type="memory.distill",
        diff_summary=f"从监督决议提炼 {len(report.added_rules)} 条风格规则",
        metadata={"added": len(report.added_rules), "skipped": report.skipped_existing},
    )
    return report
