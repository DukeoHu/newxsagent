from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from xsagent.domain.memory.patch_models import BiblePatch, RiskLevel


class FindingType(str, Enum):
    TIMELINE = "timeline"
    CHARACTER = "character"
    WORLD = "world"
    FORESHADOWING = "foreshadowing"


class Finding(BaseModel):
    id: str
    type: FindingType | str
    severity: RiskLevel
    description: str
    suggested_patch: BiblePatch | None = None


class DriftReport(BaseModel):
    findings: list[Finding] = Field(default_factory=list)


class PendingItemStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class PendingItem(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    project_id: str
    item_type: str
    risk_level: RiskLevel
    status: PendingItemStatus = PendingItemStatus.PENDING
    patch: BiblePatch | None = None
    finding: Finding | None = None
    created_at: str
    summary: str = ""
