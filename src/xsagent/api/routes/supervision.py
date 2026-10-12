from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from xsagent.core.dependencies import (
    get_action_log_service,
    get_patch_engine,
    get_pending_service,
    get_project_service,
)
from xsagent.domain.action_log.service import ActionLogService
from xsagent.domain.memory.patch_engine import PatchEngine
from xsagent.domain.quality.models import PendingItemStatus
from xsagent.domain.quality.pending_service import PendingService
from xsagent.domain.project.service import ProjectService
from xsagent.domain.memory.patch_models import RiskLevel

router = APIRouter(prefix="/api/projects/{project_id}/supervision", tags=["supervision"])


class ResolveRequest(BaseModel):
    pending_id: str
    action: str  # apply | ignore | rollback
    actor: str = "user"
    model_config = {
        "json_schema_extra": {
            "example": {"pending_id": "abc123", "action": "rollback", "actor": "author"}
        }
    }


@router.get("")
def get_supervision(
    project_id: str,
    projects: Annotated[ProjectService, Depends(get_project_service)],
    pending: Annotated[PendingService, Depends(get_pending_service)],
    logs: Annotated[ActionLogService, Depends(get_action_log_service)],
) -> dict:
    status = projects.get_status(project_id)
    pending_items = pending.list_pending(project_id)
    recent_actions = [x.model_dump() for x in logs.list_entries(project_id, limit=20)]
    health = _build_health(status.health.model_dump(), pending_items, recent_actions)
    return {
        "health": health,
        "recent_actions": recent_actions,
        "pending_items": [x.model_dump() for x in pending_items],
        "quick_links": {
            "bible": f"/projects/{project_id}/bible/characters",
            "timeline": f"/projects/{project_id}/bible/timeline",
            "graph": f"/projects/{project_id}/knowledge",
        },
    }


def _build_health(base: dict, pending_items: list, recent_actions: list[dict]) -> dict:
    low = sum(1 for p in pending_items if p.risk_level == RiskLevel.LOW)
    medium = sum(1 for p in pending_items if p.risk_level == RiskLevel.MEDIUM)
    high = sum(1 for p in pending_items if p.risk_level == RiskLevel.HIGH)
    pending_penalty = high * 25 + medium * 10 + low * 3

    pending_actions = sum(
        1
        for a in recent_actions
        if a.get("action_type", "").endswith(".pending")
    )
    session_penalty = min(40, pending_actions * 5 + high * 10)

    overall = max(0, 100 - pending_penalty)
    session = max(0, 100 - session_penalty)
    return {
        "overall": overall,
        "session": session,
        "pending_count": len(pending_items),
        "base_overall": base.get("overall", 100),
        "base_session": base.get("session", 100),
    }


@router.post("/resolve")
def resolve_supervision(
    project_id: str,
    body: ResolveRequest,
    pending: Annotated[PendingService, Depends(get_pending_service)],
    patch_engine: Annotated[PatchEngine, Depends(get_patch_engine)],
    logs: Annotated[ActionLogService, Depends(get_action_log_service)],
) -> dict:
    items = pending.list_pending(project_id)
    item = next((x for x in items if x.id == body.pending_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Pending item not found: {body.pending_id}")

    if body.action == "apply":
        if item.patch:
            patch_engine.apply(project_id, item.patch)
        pending.resolve(project_id, body.pending_id, PendingItemStatus.RESOLVED)
        logs.append(
            project_id,
            action_type="supervision.resolve",
            diff_summary=f"应用待处理项 {body.pending_id}",
            metadata={
                "pending_id": body.pending_id,
                "decision": "apply",
                "actor": body.actor,
            },
        )
        return {"ok": True, "status": "resolved"}
    if body.action == "ignore":
        pending.resolve(project_id, body.pending_id, PendingItemStatus.IGNORED)
        logs.append(
            project_id,
            action_type="supervision.resolve",
            diff_summary=f"忽略待处理项 {body.pending_id}",
            metadata={
                "pending_id": body.pending_id,
                "decision": "ignore",
                "actor": body.actor,
            },
        )
        return {"ok": True, "status": "ignored"}
    if body.action == "rollback":
        pending.resolve(project_id, body.pending_id, PendingItemStatus.IGNORED)
        logs.append(
            project_id,
            action_type="supervision.resolve",
            diff_summary=f"回滚待处理项 {body.pending_id}",
            metadata={
                "pending_id": body.pending_id,
                "decision": "rollback",
                "actor": body.actor,
            },
        )
        return {"ok": True, "status": "rolled_back"}
    raise HTTPException(status_code=400, detail="action must be apply, ignore or rollback")
