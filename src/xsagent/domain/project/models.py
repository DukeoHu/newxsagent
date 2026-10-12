from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class InterventionLevel(str, Enum):
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    genre: str = Field(default="玄幻", max_length=100)
    intervention_level: InterventionLevel = InterventionLevel.BALANCED


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    genre: str | None = Field(default=None, max_length=100)
    intervention_level: InterventionLevel | None = None


class HealthScore(BaseModel):
    overall: int = Field(ge=0, le=100)
    session: int = Field(ge=0, le=100)
    pending_count: int = Field(ge=0)


class Project(BaseModel):
    id: str
    name: str
    genre: str
    intervention_level: InterventionLevel
    created_at: str
    updated_at: str
    path: str


class ProjectStatus(BaseModel):
    project_id: str
    name: str
    health: HealthScore
    chapter_count: int
    onboarding_complete: bool
    summary: dict[str, Any]
