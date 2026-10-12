from pathlib import Path

import pytest

from xsagent.agents.maintenance import DistillAgent, DreamAgent
from xsagent.domain.memory.dream import run_heuristic_dream
from xsagent.domain.memory.service import BibleService
from xsagent.domain.project.models import ProjectCreate
from xsagent.domain.project.service import ProjectService
from xsagent.domain.quality.models import PendingItem, PendingItemStatus
from xsagent.domain.quality.pending_service import PendingService
from xsagent.domain.memory.patch_models import RiskLevel
from xsagent.domain.writing.service import ChapterService
from xsagent.llm.simulator import SimulatorProvider
from xsagent.storage.project_store import ProjectStore


def _project(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    store = ProjectStore(tmp_path / "data")
    ProjectService(store=store, template_dir=repo / "templates" / "default").create(
        ProjectCreate(name="记忆", genre="悬疑")
    )
    pid = store.list_project_ids()[0]
    return store, pid


def test_heuristic_dream_drops_orphan_summaries(tmp_path):
    store, pid = _project(tmp_path)
    bible = BibleService(store)
    chapters = ChapterService(store)
    notes = bible.get_section(pid, "notes")
    notes["chapter_summaries"] = {"ch_999": "不存在的章节"}
    notes["chapter_checkpoints"] = {"ch_999": {"chapter_id": "ch_999", "summary": "x"}}
    notes["style_rules"] = [
        {"id": "a", "title": "同一规则", "priority": "must", "category": "tone", "description": "一"},
        {"id": "b", "title": "同一规则", "priority": "must", "category": "tone", "description": "二"},
    ]
    bible.put_section(pid, "notes", notes)

    report = run_heuristic_dream(bible, chapters, pid)
    assert "ch_999" in report.orphan_summaries_removed
    assert report.duplicate_rules_removed == 1
    cleaned = bible.get_section(pid, "notes")
    assert "ch_999" not in cleaned.get("chapter_summaries", {})
    assert len(cleaned["style_rules"]) == 1


@pytest.mark.asyncio
async def test_distill_appends_style_rule_from_decisions(tmp_path):
    store, pid = _project(tmp_path)
    bible = BibleService(store)
    pending = PendingService(store)
    pending.add(
        PendingItem(
            project_id=pid,
            item_type="drift_finding",
            risk_level=RiskLevel.HIGH,
            status=PendingItemStatus.RESOLVED,
            created_at="2026-01-01T00:00:00+00:00",
            summary="拦截了提前揭晓终局的写法",
        )
    )
    agent = DistillAgent(SimulatorProvider(), bible)
    decisions = [
        f"{item.item_type}/{item.status.value}: {item.summary}"
        for item in pending.list_all(pid)
        if item.status == PendingItemStatus.RESOLVED
    ]
    report = await agent.run(pid, decisions)
    assert report.source_decisions == 1
    assert report.added_rules
    notes = bible.get_section(pid, "notes")
    assert any(rule.get("title") == "禁止提前揭晓终局" for rule in notes["style_rules"])


@pytest.mark.asyncio
async def test_dream_agent_runs_on_simulator(tmp_path):
    store, pid = _project(tmp_path)
    agent = DreamAgent(SimulatorProvider(), BibleService(store), ChapterService(store))
    report = await agent.run(pid)
    assert report.orphan_summaries_removed == []
