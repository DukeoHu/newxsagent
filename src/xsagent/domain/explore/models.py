from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ExploreOption(BaseModel):
    option_id: str
    chapter_id: str
    title: str
    summary: str
    beats: list[str]
    constraints: list[str]
    risk_level: Literal["low", "medium", "high"] = "medium"


class ExploreRecord(BaseModel):
    explore_id: str
    project_id: str
    chapter_id: str
    prompt: str
    created_at: str
    options: list[ExploreOption]
    recommended_option_id: str | None = None
    judge_reason: str = ""


class ExploreAdoptRequest(BaseModel):
    option_id: str
    actor: str = "user"


def new_explore_id() -> str:
    return uuid4().hex[:12]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()
