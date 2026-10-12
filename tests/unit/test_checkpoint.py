from pathlib import Path

import pytest

from xsagent.agents.checkpoint_writer import CheckpointWriter
from xsagent.domain.memory.service import BibleService
from xsagent.domain.project.models import ProjectCreate
from xsagent.domain.project.service import ProjectService
from xsagent.domain.writing.checkpoint import (
    CheckpointStore,
    heuristic_checkpoint,
    heuristic_summary,
    render_checkpoint,
    take_ending_slice,
)
from xsagent.domain.writing.models import ChapterCreate
from xsagent.domain.writing.service import ChapterService
from xsagent.llm.simulator import SimulatorProvider
from xsagent.storage.project_store import ProjectStore


def test_heuristic_summary_keeps_readable_spaces():
    text = "# 标题\n\n林夕推开门。柜台后的老人抬起头。"
    summary = heuristic_summary(text)
    assert "林夕" in summary
    assert " " in summary or "林夕推开门" in summary
    assert "\n" not in summary


def test_take_ending_slice_keeps_tail():
    body = "A" * 100 + "ENDING"
    assert take_ending_slice(body, 10).endswith("ENDING")


def test_checkpoint_store_roundtrip(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    store = ProjectStore(tmp_path / "data")
    ProjectService(store=store, template_dir=repo / "templates" / "default").create(
        ProjectCreate(name="test")
    )
    pid = store.list_project_ids()[0]
    bible = BibleService(store)
    checkpoints = CheckpointStore(bible)
    cp = heuristic_checkpoint("ch_001", "# 一\n\n林夕收到信。", title="第一章")
    checkpoints.put(pid, cp)

    loaded = checkpoints.get(pid, "ch_001")
    assert loaded is not None
    assert loaded.summary
    notes = bible.get_section(pid, "notes")
    assert "ch_001" in notes["chapter_summaries"]
    assert "意图" in render_checkpoint(loaded)


@pytest.mark.asyncio
async def test_checkpoint_writer_persists_structured_fields(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    store = ProjectStore(tmp_path / "data")
    ProjectService(store=store, template_dir=repo / "templates" / "default").create(
        ProjectCreate(name="test")
    )
    pid = store.list_project_ids()[0]
    chapters = ChapterService(store)
    bible = BibleService(store)
    chapters.create_chapter(
        pid,
        ChapterCreate(id="ch_002", title="第二章", content_md="# 第二章\n\n林夕走进旧邮局。"),
    )
    writer = CheckpointWriter(SimulatorProvider(), CheckpointStore(bible), chapters)
    saved = await writer.write(pid, "ch_002", "# 第二章\n\n林夕走进旧邮局。")
    assert saved.involved_characters
    assert saved.ending_slice.endswith("林夕走进旧邮局。")
    assert bible.get_section(pid, "notes")["chapter_checkpoints"]["ch_002"]["summary"]

    chapters.delete_chapter(pid, "ch_002")
    notes = bible.get_section(pid, "notes")
    assert "ch_002" not in notes.get("chapter_checkpoints", {})
    assert "ch_002" not in notes.get("chapter_summaries", {})
