from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class OnboardingSessionStatus(str, Enum):
    ACTIVE = "active"
    READY = "ready"
    APPLIED = "applied"


class OnboardingTurn(BaseModel):
    role: str = Field(pattern=r"^(assistant|user)$")
    content: str
    question_id: str | None = None


class OnboardingSession(BaseModel):
    session_id: str
    project_id: str
    status: OnboardingSessionStatus
    started_at: str
    updated_at: str
    turns: list[OnboardingTurn] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    draft: dict[str, Any] | None = None


class OnboardingQuestionResponse(BaseModel):
    session: OnboardingSession
    question: str | None = None
    question_id: str | None = None
    ready_to_generate: bool = False
    hint: str | None = None
