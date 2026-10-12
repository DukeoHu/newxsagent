from __future__ import annotations

from collections.abc import AsyncIterator
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class LLMTask(str, Enum):
    PROSE = "prose"
    BIBLE_SYNC = "bible_sync"
    DRIFT_DETECT = "drift_detect"
    FIX = "fix"
    ONBOARDING_QUESTION = "onboarding_question"
    ONBOARDING_GENERATE = "onboarding_generate"
    OUTLINE_MASTER = "outline_master"
    OUTLINE_CHAPTERS = "outline_chapters"
    OUTLINE_THREADS = "outline_threads"
    GOAL_VERIFY = "goal_verify"
    CHECKPOINT = "checkpoint"
    EXPLORE = "explore"
    JUDGE = "judge"
    DREAM = "dream"
    DISTILL = "distill"


class LLMRequest(BaseModel):
    task: LLMTask
    system: str = ""
    prompt: str
    json_mode: bool = False


class LLMProvider(Protocol):
    async def generate(self, request: LLMRequest) -> str: ...

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]: ...


class LLMResponseError(Exception):
    pass
