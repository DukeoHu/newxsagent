from xsagent.agents.checkpoint_writer import CheckpointWriter
from xsagent.agents.context import WritingContextBuilder
from xsagent.agents.prompts.defaults import DEFAULT_WRITE_INSTRUCTION
from xsagent.agents.onboarding import OnboardingAgent
from xsagent.agents.orchestrator import WriteChapterOrchestrator
from xsagent.agents.outline_planner import OutlinePlannerAgent
from xsagent.agents.explore import ExploreAgent
from xsagent.agents.goal import GoalVerifier
from xsagent.agents.maintenance import DistillAgent, DreamAgent
from xsagent.agents.prose import ProseAgent
from xsagent.agents.reviewer import ReviewerAgent
from xsagent.agents.volume_orchestrator import VolumeWriteOrchestrator
from xsagent.core.config import get_settings
from xsagent.domain.action_log.service import ActionLogService
from xsagent.domain.llm_log.service import LLMLogService
from xsagent.domain.memory.patch_engine import PatchEngine
from xsagent.domain.memory.service import BibleService
from xsagent.domain.onboarding.service import OnboardingService
from xsagent.domain.outline.planning_service import OutlinePlanningService
from xsagent.domain.outline.service import OutlineService
from xsagent.domain.project.service import ProjectService
from xsagent.domain.quality.pending_service import PendingService
from xsagent.domain.writing.compaction import CompactionService
from xsagent.domain.writing.checkpoint import CheckpointStore
from xsagent.domain.writing.service import ChapterService
from xsagent.jobs.manager import JobManager
from xsagent.jobs.models import (
    JobStatus,
    VolumeWriteRequest,
    VolumeWriteResult,
    WriteChapterRequest,
    WriteChapterResult,
)
from xsagent.llm.context import llm_call_context
from xsagent.llm.factory import get_llm_provider
from xsagent.storage.project_store import ProjectStore
from xsagent.storage.snapshot_service import SnapshotService


def get_project_store() -> ProjectStore:
    settings = get_settings()
    return ProjectStore(settings.data_dir)


def get_project_service() -> ProjectService:
    settings = get_settings()
    store = ProjectStore(settings.data_dir)
    return ProjectService(store=store, template_dir=settings.template_dir)


def get_bible_service() -> BibleService:
    return BibleService(get_project_store())


def get_onboarding_service() -> OnboardingService:
    store = get_project_store()
    return OnboardingService(
        store=store,
        projects=get_project_service(),
        bible=BibleService(store),
        agent=OnboardingAgent(get_llm_provider()),
    )


def get_chapter_service() -> ChapterService:
    return ChapterService(get_project_store())


def get_outline_service() -> OutlineService:
    return OutlineService(get_project_store())


def get_outline_planning_service() -> OutlinePlanningService:
    return OutlinePlanningService(
        projects=get_project_service(),
        bible=get_bible_service(),
        outlines=get_outline_service(),
        agent=OutlinePlannerAgent(get_llm_provider()),
    )


def get_action_log_service() -> ActionLogService:
    return ActionLogService(get_project_store())


def get_llm_log_service() -> LLMLogService:
    return LLMLogService(get_project_store())


def get_pending_service() -> PendingService:
    return PendingService(get_project_store())


def get_snapshot_service() -> SnapshotService:
    store = get_project_store()
    return SnapshotService(store=store, action_log=ActionLogService(store))


def get_patch_engine() -> PatchEngine:
    return PatchEngine(get_bible_service())


def get_write_chapter_orchestrator() -> WriteChapterOrchestrator:
    store = get_project_store()
    bible = BibleService(store)
    chapters = ChapterService(store)
    outlines = OutlineService(store)
    action_log = ActionLogService(store)
    snapshots = SnapshotService(store, action_log)
    llm = get_llm_provider()
    return WriteChapterOrchestrator(
        projects=get_project_service(),
        chapters=chapters,
        bible=bible,
        outlines=outlines,
        patch_engine=PatchEngine(bible),
        prose=ProseAgent(llm),
        reviewer=ReviewerAgent(llm),
        goal=GoalVerifier(llm),
        checkpoint_writer=CheckpointWriter(llm, CheckpointStore(bible), chapters),
        context_builder=WritingContextBuilder(store, bible, chapters, outlines),
        action_log=action_log,
        pending=PendingService(store),
        snapshots=snapshots,
        compaction=CompactionService(store, bible, chapters),
        explore=ExploreAgent(llm),
    )


def get_writing_context_builder() -> WritingContextBuilder:
    store = get_project_store()
    return WritingContextBuilder(
        store, BibleService(store), ChapterService(store), OutlineService(store)
    )


def get_explore_agent() -> ExploreAgent:
    return ExploreAgent(get_llm_provider())


def get_dream_agent() -> DreamAgent:
    store = get_project_store()
    return DreamAgent(get_llm_provider(), BibleService(store), ChapterService(store))


def get_distill_agent() -> DistillAgent:
    return DistillAgent(get_llm_provider(), get_bible_service())


class WriteChapterJobService:
    def __init__(self, orchestrator: WriteChapterOrchestrator, projects: ProjectService) -> None:
        self._orchestrator = orchestrator
        self._projects = projects

    async def run(
        self,
        project_id: str,
        request: WriteChapterRequest,
        event_cb=None,
    ) -> WriteChapterResult:
        self._projects.get_project(project_id)
        with llm_call_context(project_id=project_id):
            result = await self._orchestrator.run(
                project_id=project_id,
                instruction=request.instruction or DEFAULT_WRITE_INSTRUCTION,
                chapter_id=request.chapter_id,
                event_cb=event_cb,
                max_mode=request.max_mode,
            )
        return WriteChapterResult(job_id="sync", status=JobStatus.COMPLETED, **result)


def get_write_chapter_job_service() -> WriteChapterJobService:
    return WriteChapterJobService(
        orchestrator=get_write_chapter_orchestrator(),
        projects=get_project_service(),
    )


class VolumeWriteJobService:
    def __init__(
        self,
        orchestrator: VolumeWriteOrchestrator,
        chapter_orchestrator: WriteChapterOrchestrator,
        projects: ProjectService,
    ) -> None:
        self._orchestrator = orchestrator
        self._chapter = chapter_orchestrator
        self._projects = projects

    async def run(
        self,
        project_id: str,
        request: VolumeWriteRequest,
        event_cb=None,
    ) -> VolumeWriteResult:
        self._projects.get_project(project_id)
        with llm_call_context(project_id=project_id):
            raw = await self._orchestrator.run(
                project_id,
                request.instruction or DEFAULT_WRITE_INSTRUCTION,
                volume_id=request.volume_id,
                limit=request.limit,
                max_mode=request.max_mode,
                stop_on_revision=request.stop_on_revision,
                event_cb=event_cb,
            )
        chapter_results = [
            WriteChapterResult(job_id="sync", status=JobStatus.COMPLETED, **item)
            for item in raw["chapter_results"]
        ]
        return VolumeWriteResult(
            job_id="sync",
            status=JobStatus.COMPLETED,
            volume_id=raw.get("volume_id"),
            chapters_attempted=raw.get("chapters_attempted") or [],
            chapters_completed=raw.get("chapters_completed") or [],
            stopped_reason=raw.get("stopped_reason") or "done",
            chapter_results=chapter_results,
            goal_satisfied=bool(raw.get("goal_satisfied")),
        )


def get_volume_write_job_service() -> VolumeWriteJobService:
    chapter = get_write_chapter_orchestrator()
    store = get_project_store()
    return VolumeWriteJobService(
        orchestrator=VolumeWriteOrchestrator(
            chapter, ChapterService(store), OutlineService(store)
        ),
        chapter_orchestrator=chapter,
        projects=get_project_service(),
    )


_job_manager: JobManager | None = None


def get_job_manager() -> JobManager:
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
