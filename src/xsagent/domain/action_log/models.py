from pydantic import BaseModel, Field


class ActionLogEntry(BaseModel):
    timestamp: str
    action_type: str
    diff_summary: str = ""
    rollback_ref: str | None = None
    metadata: dict = Field(default_factory=dict)


class SnapshotInfo(BaseModel):
    id: str
    created_at: str
    label: str | None = None
    paths: list[str] = Field(default_factory=list)
