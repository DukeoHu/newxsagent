from pathlib import Path

import pytest

from xsagent.core.exceptions import ChapterAlreadyExistsError
from xsagent.domain.project.models import ProjectCreate
from xsagent.domain.project.service import ProjectService
from xsagent.domain.writing.models import ChapterCreate, ChapterUpdate
from xsagent.domain.writing.service import ChapterService
from xsagent.storage.project_store import ProjectStore


@pytest.fixture
def chapter_ctx(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    store = ProjectStore(tmp_path / "data")
    ProjectService(store=store, template_dir=repo / "templates" / "default").create(
        ProjectCreate(name="test")
    )
    pid = store.list_project_ids()[0]
    return ChapterService(store), pid


def test_create_and_count_words(chapter_ctx):
    service, pid = chapter_ctx
    chapter = service.create_chapter(
        pid, ChapterCreate(id="ch_002", title="第二章", content_md="# 第二章\n\n这是正文。")
    )
    assert chapter.word_count > 0
    assert chapter.title == "第二章"


def test_duplicate_chapter(chapter_ctx):
    service, pid = chapter_ctx
    with pytest.raises(ChapterAlreadyExistsError):
        service.create_chapter(pid, ChapterCreate(id="ch_001"))


def test_update_chapter(chapter_ctx):
    service, pid = chapter_ctx
    updated = service.update_chapter(
        pid, "ch_001", ChapterUpdate(title="新标题", content_md="# 新标题\n\n新内容。")
    )
    assert updated.title == "新标题"
    assert "新内容" in updated.content_md


def test_delete_chapter(chapter_ctx):
    service, pid = chapter_ctx
    service.create_chapter(
        pid, ChapterCreate(id="ch_002", title="第二章", content_md="# 第二章\n\n正文。")
    )
    service.delete_chapter(pid, "ch_002")
    summaries = service.list_chapters(pid)
    assert [chapter.id for chapter in summaries] == ["ch_001"]
