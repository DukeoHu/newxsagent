import asyncio
import time
from datetime import UTC, datetime
from uuid import uuid4

from xsagent.jobs.models import (
    JobEvent,
    JobRecord,
    JobStatus,
    VolumeWriteResult,
    WriteChapterRequest,
    WriteChapterResult,
)
from xsagent.llm.context import llm_call_context


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()

    async def submit_write_job(self, project_id: str, request: WriteChapterRequest, runner) -> str:
        async def _wrapped(event_cb):
            return await runner(project_id, request, event_cb)

        return await self.submit_job(project_id, _wrapped, job_type="write-chapter")

    async def submit_job(self, project_id: str, runner, *, job_type: str) -> str:
        job_id = uuid4().hex[:12]
        now = datetime.now(UTC).isoformat()
        record = JobRecord(
            id=job_id,
            project_id=project_id,
            status=JobStatus.PENDING,
            created_at=now,
            updated_at=now,
            job_type=job_type,
        )
        async with self._lock:
            self._jobs[job_id] = record
        asyncio.create_task(self._run_job(job_id, project_id, runner))
        return job_id

    async def _run_job(self, job_id: str, project_id: str, runner) -> None:
        await self._set_status(job_id, JobStatus.RUNNING)
        await self.add_event(job_id, "job.progress", {"stage": "start", "percent": 5})
        try:
            async def _event_cb(event_type: str, data: dict) -> None:
                await self.add_event(job_id, event_type, data)

            with llm_call_context(project_id=project_id, job_id=job_id):
                result = await runner(_event_cb)
            await self.add_event(job_id, "job.complete", _complete_payload(result))
            await self._finish(job_id, result)
        except Exception as exc:  # noqa: BLE001
            await self.add_event(job_id, "job.error", {"message": str(exc)})
            await self._fail(job_id, str(exc))

    async def add_event(self, job_id: str, event_type: str, data: dict) -> None:
        async with self._lock:
            record = self._jobs[job_id]
            record.events.append(JobEvent(type=event_type, data=data, ts=time.time()))
            record.updated_at = datetime.now(UTC).isoformat()

    async def _set_status(self, job_id: str, status: JobStatus) -> None:
        async with self._lock:
            record = self._jobs[job_id]
            record.status = status
            record.updated_at = datetime.now(UTC).isoformat()

    async def _finish(self, job_id: str, result: WriteChapterResult | VolumeWriteResult) -> None:
        async with self._lock:
            record = self._jobs[job_id]
            record.status = JobStatus.COMPLETED
            record.result = result
            record.updated_at = datetime.now(UTC).isoformat()

    async def _fail(self, job_id: str, message: str) -> None:
        async with self._lock:
            record = self._jobs[job_id]
            record.status = JobStatus.FAILED
            record.error = message
            record.updated_at = datetime.now(UTC).isoformat()

    async def get_job(self, job_id: str) -> JobRecord | None:
        async with self._lock:
            return self._jobs.get(job_id)


def _complete_payload(result: WriteChapterResult | VolumeWriteResult) -> dict:
    if isinstance(result, VolumeWriteResult):
        return {
            "kind": "volume",
            "chapters_completed": result.chapters_completed,
            "chapters_attempted": result.chapters_attempted,
            "stopped_reason": result.stopped_reason,
            "goal_satisfied": result.goal_satisfied,
        }
    return {
        "kind": "chapter",
        "chapter_id": result.chapter_id,
        "word_count": result.word_count,
        "goal_satisfied": result.goal_satisfied,
        "blueprint_status": result.blueprint_status,
        "goal_summary": result.goal_summary,
        "max_mode_used": result.max_mode_used,
    }
