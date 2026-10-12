from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from xsagent.domain.memory.patch_models import BiblePatch, PatchApplyResult


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WriteChapterRequest(BaseModel):
    instruction: str | None = None
    chapter_id: str | None = Field(default=None, pattern=r"^ch_\d{3,}$")
    max_mode: bool | None = None
    model_config = {
        "json_schema_extra": {
            "example": {"instruction": "继续写下一章", "chapter_id": "ch_002"}
        }
    }


class VolumeWriteRequest(BaseModel):
    instruction: str | None = None
    volume_id: str | None = None
    limit: int = Field(default=3, ge=1, le=8)
    max_mode: bool | None = None
    stop_on_revision: bool = True


class WriteChapterResult(BaseModel):
    kind: Literal["chapter"] = "chapter"
    job_id: str
    status: JobStatus
    chapter_id: str
    word_count: int
    sync_patch: BiblePatch | None = None
    sync_apply: PatchApplyResult | None = None
    drift_findings_count: int = 0
    pending_ids: list[str] = Field(default_factory=list)
    compacted: bool = False
    actions_logged: list[str] = Field(default_factory=list)
    goal_satisfied: bool = True
    goal_impossible: bool = False
    goal_summary: str = ""
    blueprint_status: str = "completed"
    rewrite_count: int = 0
    checkpointed: bool = False
    max_mode_used: bool = False
    selected_plan: str = ""


class VolumeWriteResult(BaseModel):
    kind: Literal["volume"] = "volume"
    job_id: str
    status: JobStatus
    volume_id: str | None = None
    chapters_attempted: list[str] = Field(default_factory=list)
    chapters_completed: list[str] = Field(default_factory=list)
    stopped_reason: str = "done"
    chapter_results: list[WriteChapterResult] = Field(default_factory=list)
    goal_satisfied: bool = True


class PatchPreviewRequest(BaseModel):
    patch: BiblePatch
    apply: bool = False


class JobEvent(BaseModel):
    type: str
    data: dict[str, Any] = Field(default_factory=dict)
    ts: float


class JobRecord(BaseModel):
    id: str
    project_id: str
    status: JobStatus
    created_at: str
    updated_at: str
    job_type: str = "write-chapter"
    result: WriteChapterResult | VolumeWriteResult | None = None
    error: str | None = None
    events: list[JobEvent] = Field(default_factory=list)


class JobSubmitResponse(BaseModel):
    job_id: str
    status: JobStatus
    model_config = {
        "json_schema_extra": {"example": {"job_id": "a1b2c3d4e5f6", "status": "pending"}}
    }
