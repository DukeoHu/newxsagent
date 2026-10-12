from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PatchUpdate(BaseModel):
    section: str
    op: Literal["set", "append", "merge"] = "set"
    path: str
    value: Any


class BiblePatch(BaseModel):
    updates: list[PatchUpdate] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    explanation: str = ""
    source_chapter: str | None = None


class PatchPreview(BaseModel):
    section: str
    before: dict[str, Any]
    after: dict[str, Any]
    changed_paths: list[str]


class PatchApplyResult(BaseModel):
    applied: bool
    previews: list[PatchPreview] = Field(default_factory=list)
    risk_level: RiskLevel
    explanation: str
    auto_applied: bool = False
    pending_id: str | None = None
