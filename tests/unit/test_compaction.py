import pytest

from xsagent.domain.project.models import ProjectCreate
from xsagent.domain.project.service import ProjectService
from xsagent.domain.writing.compaction import CompactionService
from xsagent.domain.memory.service import BibleService
from xsagent.domain.writing.service import ChapterService
from xsagent.domain.writing.models import ChapterCreate
from xsagent.storage.project_store import ProjectStore


def test_compaction_on_tenth_chapter(tmp_path):
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    store = ProjectStore(tmp_path / "data")
    ProjectService(store=store, template_dir=repo / "templates" / "default").create(
        ProjectCreate(name="test")
    )
    pid = store.list_project_ids()[0]
    chapters = ChapterService(store)
    bible = BibleService(store)
    compaction = CompactionService(store, bible, chapters)

    for i in range(2, 11):
        chapters.create_chapter(
            pid,
            ChapterCreate(id=f"ch_{i:03d}", content_md=f"# 第{i}章\n\n内容{i}" * 5),
        )

    assert compaction.maybe_compact(pid) is True
    notes = bible.get_section(pid, "notes")
    assert "chapter_summaries" in notes
    assert len(notes["chapter_summaries"]) >= 1
    assert "chapter_checkpoints" in notes
    first_id = next(iter(notes["chapter_checkpoints"]))
    sample = notes["chapter_checkpoints"][first_id]
    assert sample["ending_slice"]
    assert sample["summary"]
    assert notes["chapter_summaries"][first_id] == sample["summary"]
