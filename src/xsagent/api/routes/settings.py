from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from xsagent.core.config import get_llm_runtime_config, update_llm_runtime_config

router = APIRouter(prefix="/api/settings", tags=["settings"])


class LLMConfigResponse(BaseModel):
    mode: str
    ollama_base_url: str
    ollama_model: str
    ollama_think: bool
    strip_think_tags: bool
    deepseek_base_url: str
    deepseek_api_key: str
    deepseek_model: str
    deepseek_reasoning_effort: str
    deepseek_thinking_enabled: bool


class LLMConfigUpdateRequest(BaseModel):
    mode: Literal["simulator", "ollama", "deepseek"] = Field(default="ollama")
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="deepseek-r1:latest")
    ollama_think: bool = Field(default=True)
    strip_think_tags: bool = Field(default=True)
    deepseek_base_url: str = Field(default="https://api.deepseek.com")
    deepseek_api_key: str = Field(default="")
    deepseek_model: str = Field(default="deepseek-v4-pro")
    deepseek_reasoning_effort: str = Field(default="high")
    deepseek_thinking_enabled: bool = Field(default=True)


@router.get("/llm", response_model=LLMConfigResponse)
def get_llm_config() -> LLMConfigResponse:
    return LLMConfigResponse.model_validate(get_llm_runtime_config())


@router.put("/llm", response_model=LLMConfigResponse)
def put_llm_config(body: LLMConfigUpdateRequest) -> LLMConfigResponse:
    updated = update_llm_runtime_config(body.model_dump())
    return LLMConfigResponse.model_validate(updated)
