from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_project_id: ContextVar[str | None] = ContextVar("llm_project_id", default=None)
_job_id: ContextVar[str | None] = ContextVar("llm_job_id", default=None)


def get_llm_context() -> tuple[str | None, str | None]:
    return _project_id.get(), _job_id.get()


@contextmanager
def llm_call_context(
    *,
    project_id: str | None = None,
    job_id: str | None = None,
) -> Iterator[None]:
    tokens: list[tuple[ContextVar[str | None], object]] = []
    if project_id is not None:
        tokens.append((_project_id, _project_id.set(project_id)))
    if job_id is not None:
        tokens.append((_job_id, _job_id.set(job_id)))
    try:
        yield
    finally:
        for var, token in reversed(tokens):
            var.reset(token)
