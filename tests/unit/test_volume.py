from pathlib import Path

import pytest

from xsagent.agents.checkpoint_writer import CheckpointWriter
from xsagent.agents.context import WritingContextBuilder
from xsagent.agents.explore import ExploreAgent
from xsagent.agents.goal import GoalVerifier
from xsagent.agents.orchestrator import WriteChapterOrchestrator
from xsagent.agents.prose import ProseAgent
from xsagent.agents.reviewer import ReviewerAgent
from xsagent.agents.volume_orchestrator import VolumeWriteOrchestrator
from xsagent.domain.action_log.service import ActionLogService
from xsagent.domain.memory.patch_engine import PatchEngine
from xsagent.domain.memory.service import BibleService
from xsagent.domain.outline.service import OutlineService
from xsagent.domain.project.models import ProjectCreate
from xsagent.domain.project.service import ProjectService
from xsagent.domain.quality.pending_service import PendingService
from xsagent.domain.writing.checkpoint import CheckpointStore
from xsagent.domain.writing.compaction import CompactionService
from xsagent.domain.writing.service import ChapterService
from xsagent.llm.simulator import SimulatorProvider
from xsagent.storage.project_store import ProjectStore
from xsagent.storage.snapshot_service import SnapshotService


def _chapter_orch(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    store = ProjectStore(tmp_path / "data")
    ps = ProjectService(store=store, template_dir=repo / "templates" / "default")
    project = ps.create(ProjectCreate(name="连写", genre="悬疑"))
    pid = project.id
    bible = BibleService(store)
    chapters = ChapterService(store)
    outlines = OutlineService(store)
    llm = SimulatorProvider()
    orch = WriteChapterOrchestrator(
        projects=ps,
        chapters=chapters,
        bible=bible,
        outlines=outlines,
        patch_engine=PatchEngine(bible),
        prose=ProseAgent(llm),
        reviewer=ReviewerAgent(llm),
        goal=GoalVerifier(llm),
        checkpoint_writer=CheckpointWriter(llm, CheckpointStore(bible), chapters),
        context_builder=WritingContextBuilder(store, bible, chapters, outlines),
        action_log=ActionLogService(store),
        pending=PendingService(store),
        snapshots=SnapshotService(store, ActionLogService(store)),
        compaction=CompactionService(store, bible, chapters),
        explore=ExploreAgent(llm),
    )
    return orch, pid, chapters, outlines


@pytest.mark.asyncio
async def test_volume_write_loops_two_chapters(tmp_path):
    chapter_orch, pid, chapters, _outlines = _chapter_orch(tmp_path)
    volume = VolumeWriteOrchestrator(chapter_orch, chapters, _outlines)
    result = await volume.run(pid, "继续写", limit=2)
    assert result["stopped_reason"] == "done"
    assert len(result["chapters_completed"]) == 2
    assert result["goal_satisfied"] is True
    ids = [item.id for item in chapters.list_chapters(pid)]
    assert "ch_001" in ids
    assert "ch_002" in ids


@pytest.mark.asyncio
async def test_max_mode_selects_a_plan(tmp_path):
    orch, pid, _, _outlines = _chapter_orch(tmp_path)
    result = await orch.run(pid, "写高潮", max_mode=True)
    assert result["max_mode_used"] is True
    assert result["selected_plan"]
    assert "方案" in result["selected_plan"]
