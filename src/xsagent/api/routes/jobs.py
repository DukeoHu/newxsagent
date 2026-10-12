import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from xsagent.core.dependencies import (
    WriteChapterJobService,
    VolumeWriteJobService,
    get_job_manager,
    get_pending_service,
    get_volume_write_job_service,
    get_write_chapter_job_service,
)
from xsagent.core.exceptions import ProjectNotFoundError
from xsagent.domain.quality.models import PendingItem
from xsagent.domain.quality.pending_service import PendingService
from xsagent.jobs.manager import JobManager
from xsagent.jobs.models import (
    JobRecord,
    JobStatus,
    JobSubmitResponse,
    VolumeWriteRequest,
    WriteChapterRequest,
    WriteChapterResult,
)

router = APIRouter(prefix="/api/projects/{project_id}", tags=["jobs"])


@router.post("/jobs/write-chapter-sync", response_model=WriteChapterResult)
async def write_chapter_sync(
    project_id: str,
    body: WriteChapterRequest,
    service: Annotated[WriteChapterJobService, Depends(get_write_chapter_job_service)],
) -> WriteChapterResult:
    try:
        result = await service.run(project_id, body)
        if result.status == JobStatus.FAILED:
            raise HTTPException(status_code=500, detail=result.actions_logged)
        return result
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/pending", response_model=list[PendingItem])
def list_pending(
    project_id: str,
    service: Annotated[PendingService, Depends(get_pending_service)],
) -> list[PendingItem]:
    return service.list_pending(project_id)


@router.post("/jobs/write-chapter-submit", response_model=JobSubmitResponse, status_code=202)
async def submit_write_job(
    project_id: str,
    body: WriteChapterRequest,
    job_manager: Annotated[JobManager, Depends(get_job_manager)],
    service: Annotated[WriteChapterJobService, Depends(get_write_chapter_job_service)],
) -> JobSubmitResponse:
    async def _runner(pid: str, req: WriteChapterRequest, event_cb):
        return await service.run(pid, req, event_cb=event_cb)

    job_id = await job_manager.submit_write_job(project_id, body, _runner)
    return JobSubmitResponse(job_id=job_id, status=JobStatus.PENDING)


@router.post("/jobs/write-chapter", response_model=JobSubmitResponse, status_code=202)
async def submit_write_job_default(
    project_id: str,
    body: WriteChapterRequest,
    job_manager: Annotated[JobManager, Depends(get_job_manager)],
    service: Annotated[WriteChapterJobService, Depends(get_write_chapter_job_service)],
) -> JobSubmitResponse:
    async def _runner(pid: str, req: WriteChapterRequest, event_cb):
        return await service.run(pid, req, event_cb=event_cb)

    job_id = await job_manager.submit_write_job(project_id, body, _runner)
    return JobSubmitResponse(job_id=job_id, status=JobStatus.PENDING)


@router.post("/jobs/write-volume", response_model=JobSubmitResponse, status_code=202)
async def submit_volume_write_job(
    project_id: str,
    body: VolumeWriteRequest,
    job_manager: Annotated[JobManager, Depends(get_job_manager)],
    service: Annotated[VolumeWriteJobService, Depends(get_volume_write_job_service)],
) -> JobSubmitResponse:
    async def _runner(event_cb):
        return await service.run(project_id, body, event_cb=event_cb)

    job_id = await job_manager.submit_job(project_id, _runner, job_type="write-volume")
    return JobSubmitResponse(job_id=job_id, status=JobStatus.PENDING)


@router.get("/jobs/{job_id}", response_model=JobRecord)
async def get_job(
    project_id: str,
    job_id: str,
    job_manager: Annotated[JobManager, Depends(get_job_manager)],
) -> JobRecord:
    job = await job_manager.get_job(job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return job


@router.get("/jobs/{job_id}/events")
async def stream_job_events(
    project_id: str,
    job_id: str,
    job_manager: Annotated[JobManager, Depends(get_job_manager)],
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    async def event_stream():
        sent = 0
        if last_event_id is not None and last_event_id.isdigit():
            sent = max(0, int(last_event_id) + 1)
        while True:
            job = await job_manager.get_job(job_id)
            if job is None or job.project_id != project_id:
                yield "event: job.error\ndata: {\"message\":\"job not found\"}\n\n"
                break
            while sent < len(job.events):
                evt = job.events[sent]
                evt_id = sent
                sent += 1
                yield f"id: {evt_id}\nevent: {evt.type}\ndata: {evt.model_dump_json()}\n\n"
            if job.status in {JobStatus.COMPLETED, JobStatus.FAILED}:
                break
            await asyncio.sleep(0.3)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
