from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from xsagent.core.dependencies import get_onboarding_service
from xsagent.core.exceptions import ProjectNotFoundError
from xsagent.domain.onboarding.models import OnboardingQuestionResponse, OnboardingSession
from xsagent.domain.onboarding.service import OnboardingService

router = APIRouter(prefix="/api/projects/{project_id}", tags=["onboarding"])


class OnboardingApplyRequest(BaseModel):
    bible: dict


class OnboardingAnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=4000)


class OnboardingDraftResponse(BaseModel):
    project_id: str
    draft: dict
    llm_mode: str
    warning: str | None = None


@router.get("/onboarding/session", response_model=OnboardingSession | None)
def get_onboarding_session(
    project_id: str,
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> OnboardingSession | None:
    try:
        return service.get_session(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/onboarding/start", response_model=OnboardingQuestionResponse)
async def start_onboarding(
    project_id: str,
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> OnboardingQuestionResponse:
    try:
        return await service.start_session(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/onboarding/answer", response_model=OnboardingQuestionResponse)
async def answer_onboarding(
    project_id: str,
    body: OnboardingAnswerRequest,
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> OnboardingQuestionResponse:
    try:
        return await service.submit_answer(project_id, body.answer)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/onboarding", response_model=OnboardingDraftResponse)
async def generate_onboarding(
    project_id: str,
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> OnboardingDraftResponse:
    try:
        draft = await service.generate_draft(project_id)
        return OnboardingDraftResponse(
            project_id=project_id,
            draft=draft,
            llm_mode=service.current_llm_mode(),
            warning=service.generation_warning(),
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/onboarding/apply")
def apply_onboarding(
    project_id: str,
    body: OnboardingApplyRequest,
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> dict:
    try:
        service.apply_draft(project_id, body.bible)
        return {"ok": True}
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/onboarding/clear-draft", response_model=OnboardingSession)
def clear_onboarding_draft(
    project_id: str,
    service: Annotated[OnboardingService, Depends(get_onboarding_service)],
) -> OnboardingSession:
    try:
        return service.clear_draft(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
