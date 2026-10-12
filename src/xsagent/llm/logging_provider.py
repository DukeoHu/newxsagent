from __future__ import annotations

import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import uuid4

from xsagent.core.config import Settings
from xsagent.domain.llm_log.models import LLMLogEntry
from xsagent.domain.llm_log.service import LLMLogService
from xsagent.llm.base import LLMProvider, LLMRequest
from xsagent.llm.context import get_llm_context


class LoggingLLMProvider:
    """Wrap an LLM provider and persist request/response payloads per project."""

    def __init__(
        self,
        inner: LLMProvider,
        log_service: LLMLogService,
        settings: Settings,
    ) -> None:
        self._inner = inner
        self._log_service = log_service
        self._settings = settings

    def _model_name(self) -> str:
        mode = self._settings.llm_mode.lower()
        if mode == "ollama":
            return self._settings.ollama_model
        if mode == "deepseek":
            return self._settings.deepseek_model
        return "simulator"

    def _truncate(self, text: str) -> tuple[str, bool]:
        max_chars = self._settings.llm_log_max_chars
        if len(text) <= max_chars:
            return text, False
        return text[:max_chars] + "\n…[truncated]", True

    def _should_log(self) -> tuple[bool, str | None, str | None]:
        if not self._settings.llm_log_enabled:
            return False, None, None
        project_id, job_id = get_llm_context()
        if not project_id:
            return False, None, None
        return True, project_id, job_id

    def _write_log(
        self,
        *,
        project_id: str,
        job_id: str | None,
        request: LLMRequest,
        response: str | None,
        error: str | None,
        latency_ms: int,
        status: str,
    ) -> None:
        system, system_truncated = self._truncate(request.system)
        prompt, prompt_truncated = self._truncate(request.prompt)
        response_text, response_truncated = self._truncate(response or "")

        entry = LLMLogEntry(
            id=uuid4().hex[:12],
            timestamp=datetime.now(UTC).isoformat(),
            project_id=project_id,
            job_id=job_id,
            task=request.task.value,
            llm_mode=self._settings.llm_mode,
            model=self._model_name(),
            system=system,
            prompt=prompt,
            json_mode=request.json_mode,
            response=response_text if response is not None else None,
            error=error,
            latency_ms=latency_ms,
            status=status,
            system_truncated=system_truncated,
            prompt_truncated=prompt_truncated,
            response_truncated=response_truncated,
        )
        self._log_service.append(project_id, entry)

    async def generate(self, request: LLMRequest) -> str:
        should_log, project_id, job_id = self._should_log()
        if not should_log:
            return await self._inner.generate(request)

        started = time.perf_counter()
        response: str | None = None
        error: str | None = None
        status = "ok"
        try:
            response = await self._inner.generate(request)
            return response
        except Exception as exc:
            status = "error"
            error = str(exc)
            raise
        finally:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self._write_log(
                project_id=project_id,
                job_id=job_id,
                request=request,
                response=response,
                error=error,
                latency_ms=latency_ms,
                status=status,
            )

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        should_log, project_id, job_id = self._should_log()
        if not should_log:
            async for chunk in self._inner.stream(request):
                yield chunk
            return

        started = time.perf_counter()
        chunks: list[str] = []
        error: str | None = None
        status = "ok"
        try:
            async for chunk in self._inner.stream(request):
                chunks.append(chunk)
                yield chunk
        except Exception as exc:
            status = "error"
            error = str(exc)
            raise
        finally:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self._write_log(
                project_id=project_id,
                job_id=job_id,
                request=request,
                response="".join(chunks) if chunks else None,
                error=error,
                latency_ms=latency_ms,
                status=status,
            )
