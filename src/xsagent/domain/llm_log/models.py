from pydantic import BaseModel, Field


class LLMLogEntry(BaseModel):
    id: str
    timestamp: str
    project_id: str | None = None
    job_id: str | None = None
    task: str
    llm_mode: str
    model: str
    system: str = ""
    prompt: str
    json_mode: bool = False
    response: str | None = None
    error: str | None = None
    latency_ms: int = 0
    status: str = "ok"
    system_truncated: bool = False
    prompt_truncated: bool = False
    response_truncated: bool = False
    metadata: dict = Field(default_factory=dict)
