from pathlib import Path

import pytest

from xsagent.agents.checkpoint_writer import CheckpointWriter
from xsagent.agents.context import WritingContextBuilder
from xsagent.agents.goal import GoalVerifier
from xsagent.agents.orchestrator import WriteChapterOrchestrator
from xsagent.agents.prose import ProseAgent
from xsagent.agents.reviewer import ReviewerAgent
from xsagent.domain.action_log.service import ActionLogService
from xsagent.domain.memory.patch_engine import PatchEngine
from xsagent.domain.memory.service import BibleService
from xsagent.domain.outline.service import OutlineService
from xsagent.domain.project.models import ProjectCreate
from xsagent.domain.project.service import ProjectService
from xsagent.domain.quality.goal import GoalGap, GoalVerdict
from xsagent.domain.quality.pending_service import PendingService
from xsagent.domain.writing.checkpoint import CheckpointStore
from xsagent.domain.writing.compaction import CompactionService
from xsagent.domain.writing.service import ChapterService
from xsagent.llm.simulator import SimulatorProvider
from xsagent.storage.project_store import ProjectStore
from xsagent.storage.snapshot_service import SnapshotService


def _build_orchestrator(tmp_path, goal=None, llm=None, **kwargs):
    repo = Path(__file__).resolve().parents[2]
    store = ProjectStore(tmp_path / "data")
    ps = ProjectService(store=store, template_dir=repo / "templates" / "default")
    project = ps.create(ProjectCreate(name="测试", genre="悬疑"))
    pid = project.id

    bible = BibleService(store)
    chapters = ChapterService(store)
    outlines = OutlineService(store)
    action_log = ActionLogService(store)
    provider = llm or SimulatorProvider()

    orch = WriteChapterOrchestrator(
        projects=ps,
        chapters=chapters,
        bible=bible,
        outlines=outlines,
        patch_engine=PatchEngine(bible),
        prose=ProseAgent(provider),
        reviewer=ReviewerAgent(provider),
        goal=goal or GoalVerifier(provider),
        checkpoint_writer=CheckpointWriter(provider, CheckpointStore(bible), chapters),
        context_builder=WritingContextBuilder(store, bible, chapters, outlines),
        action_log=action_log,
        pending=PendingService(store),
        snapshots=SnapshotService(store, action_log),
        compaction=CompactionService(store, bible, chapters),
        **kwargs,
    )
    return orch, pid, bible, action_log, outlines


class _FailThenPassGoal:
    def __init__(self) -> None:
        self.calls = 0

    async def verify(self, **kwargs) -> GoalVerdict:
        del kwargs
        self.calls += 1
        if self.calls == 1:
            return GoalVerdict(
                satisfied=False,
                gaps=[GoalGap(code="beats", detail="未写出章末钩子")],
                summary="缺收束",
            )
        return GoalVerdict(satisfied=True, summary="已补上钩子")


class _AlwaysFailGoal:
    async def verify(self, **kwargs) -> GoalVerdict:
        del kwargs
        return GoalVerdict(
            satisfied=False,
            gaps=[GoalGap(code="beats", detail="未覆盖蓝图")],
            summary="未完成",
        )


@pytest.mark.asyncio
async def test_write_chapter_pipeline(tmp_path):
    orch, pid, bible, action_log, outlines = _build_orchestrator(tmp_path)
    result = await orch.run(pid, "继续写下一章")

    assert result["word_count"] > 0
    chars = bible.get_section(pid, "characters")
    assert len(chars["characters"]) >= 1
    assert result["sync_apply"] is not None
    assert result["drift_findings_count"] >= 1
    assert len(result["pending_ids"]) >= 1
    assert result["goal_satisfied"] is True
    assert result["blueprint_status"] == "completed"
    assert result["checkpointed"] is True
    assert result["rewrite_count"] == 0

    notes = bible.get_section(pid, "notes")
    assert result["chapter_id"] in notes.get("chapter_checkpoints", {})

    logs = action_log.list_entries(pid)
    types = {log.action_type for log in logs}
    assert "write.chapter" in types
    assert "bible_sync.apply" in types
    assert "drift_fix.pending" in types

    blueprint = outlines.get_chapter_blueprint(pid, result["chapter_id"])
    assert blueprint.status == "completed"


@pytest.mark.asyncio
async def test_goal_failure_rewrites_once_then_passes(tmp_path):
    goal = _FailThenPassGoal()
    orch, pid, _, _, outlines = _build_orchestrator(tmp_path, goal=goal)
    result = await orch.run(pid, "继续写下一章")

    assert goal.calls == 2
    assert result["rewrite_count"] == 1
    assert result["goal_satisfied"] is True
    assert outlines.get_chapter_blueprint(pid, result["chapter_id"]).status == "completed"


@pytest.mark.asyncio
async def test_goal_failure_marks_needs_revision(tmp_path):
    orch, pid, _, action_log, outlines = _build_orchestrator(
        tmp_path, goal=_AlwaysFailGoal(), goal_rewrite_limit=0
    )
    result = await orch.run(pid, "继续写下一章")

    assert result["goal_satisfied"] is False
    assert result["blueprint_status"] == "needs_revision"
    assert outlines.get_chapter_blueprint(pid, result["chapter_id"]).status == "needs_revision"
    types = {log.action_type for log in action_log.list_entries(pid)}
    assert "goal_gap.pending" in types
