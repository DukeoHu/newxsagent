from pathlib import Path

import pytest

from xsagent.agents.context import (
    ROLLING_WINDOW_SIZE,
    WritingContextBuilder,
    chapter_number,
    trim_chapter_for_context,
)
from xsagent.domain.memory.service import BibleService
from xsagent.domain.outline.service import OutlineService
from xsagent.domain.project.models import ProjectCreate
from xsagent.domain.project.service import ProjectService
from xsagent.domain.writing.models import ChapterCreate, ChapterUpdate
from xsagent.domain.writing.service import ChapterService
from xsagent.storage.project_store import ProjectStore


@pytest.fixture
def context_setup(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    store = ProjectStore(tmp_path / "data")
    projects = ProjectService(store=store, template_dir=repo / "templates" / "default")
    project = projects.create(ProjectCreate(name="滚动窗口", genre="玄幻"))
    pid = project.id
    chapters = ChapterService(store)
    bible = BibleService(store)
    builder = WritingContextBuilder(store, bible, chapters, OutlineService(store))
    return builder, projects, chapters, bible, pid, project


def test_chapter_number_parses_ids():
    assert chapter_number("ch_001") == 1
    assert chapter_number("ch_1000") == 1000


def test_trim_chapter_keeps_head_and_tail():
    body = "A" * 500 + "MIDDLE" + "B" * 500
    trimmed = trim_chapter_for_context(body, 600)
    assert trimmed.startswith("A" * 150)
    assert trimmed.endswith("B" * 430)
    assert "中段省略" in trimmed


def test_rolling_window_empty_for_first_chapter(context_setup):
    builder, _, _, _, pid, project = context_setup
    ctx = builder.build(project, "ch_001", "继续写")
    assert "尚无已写章节" in ctx["recent_chapters_window"]


def test_rolling_window_includes_prior_chapters(context_setup):
    builder, _, chapters, _, pid, project = context_setup

    chapters.update_chapter(
        pid,
        "ch_001",
        ChapterUpdate(content_md="# 第一章\n\n开端情节。"),
    )
    chapters.create_chapter(
        pid,
        ChapterCreate(
            id="ch_002",
            title="第二章",
            content_md="# 第二章\n\n林夕进入旧邮局。",
        ),
    )
    chapters.create_chapter(
        pid,
        ChapterCreate(
            id="ch_003",
            title="第三章",
            content_md="# 第三章\n\n神秘老人现身。",
        ),
    )

    ctx = builder.build(project, "ch_004", "继续写下一章")
    window = ctx["recent_chapters_window"]

    assert "ch_001" in window
    assert "ch_002" in window
    assert "ch_003" in window
    assert "神秘老人现身" in window
    assert "林夕进入旧邮局" in window
    assert "ch_004" not in window
    assert "章末切片" in window


def test_rolling_window_caps_at_three(context_setup):
    builder, _, chapters, _, pid, project = context_setup

    chapters.update_chapter(
        pid,
        "ch_001",
        ChapterUpdate(content_md="# 第1章\n\n内容1。"),
    )
    for i in range(2, 6):
        cid = f"ch_{i:03d}"
        chapters.create_chapter(
            pid,
            ChapterCreate(id=cid, title=f"第{i}章", content_md=f"# 第{i}章\n\n内容{i}。"),
        )

    ctx = builder.build(project, "ch_006", "继续")
    window = ctx["recent_chapters_window"]

    assert "ch_002" not in window
    assert "ch_003" in window
    assert "ch_004" in window
    assert "ch_005" in window
    assert window.count("### ch_") == ROLLING_WINDOW_SIZE


def test_rolling_window_uses_stored_summary_for_older_chapter(context_setup):
    builder, _, chapters, bible, pid, project = context_setup

    chapters.update_chapter(
        pid,
        "ch_001",
        ChapterUpdate(content_md="# 第1章\n\n长内容1。"),
    )
    for i in range(2, 4):
        cid = f"ch_{i:03d}"
        chapters.create_chapter(
            pid,
            ChapterCreate(id=cid, title=f"第{i}章", content_md=f"# 第{i}章\n\n长内容{i}。"),
        )

    notes = bible.get_section(pid, "notes")
    notes["chapter_summaries"] = {"ch_001": "第一章摘要：林夕收到信。"}
    bible.put_section(pid, "notes", notes)

    ctx = builder.build(project, "ch_004", "继续")
    window = ctx["recent_chapters_window"]

    assert "第一章摘要：林夕收到信。" in window
    assert "压缩摘要" in window


def test_immediate_prior_uses_ending_slice_even_when_summary_exists(context_setup):
    builder, _, chapters, bible, pid, project = context_setup

    chapters.update_chapter(
        pid,
        "ch_001",
        ChapterUpdate(content_md="# 第1章\n\n长内容1。"),
    )
    for i in range(2, 4):
        cid = f"ch_{i:03d}"
        chapters.create_chapter(
            pid,
            ChapterCreate(id=cid, title=f"第{i}章", content_md=f"# 第{i}章\n\n长内容{i}独有结尾。"),
        )

    notes = bible.get_section(pid, "notes")
    notes["chapter_summaries"] = {
        "ch_001": "摘要1",
        "ch_002": "摘要2",
        "ch_003": "摘要3不应替代章末切片",
    }
    bible.put_section(pid, "notes", notes)

    ctx = builder.build(project, "ch_004", "继续")
    window = ctx["recent_chapters_window"]

    assert "摘要1" in window
    assert "摘要3不应替代章末切片" not in window
    assert "长内容3独有结尾" in window
    assert "章末切片" in window
    assert ctx["session_checkpoint"]


def test_writing_context_includes_style_rules(context_setup):
    builder, _, _, bible, pid, project = context_setup
    notes = bible.get_section(pid, "notes")
    notes["style_notes"] = "冷峻悬疑"
    notes["style_rules"] = [
        {
            "id": "sr_1",
            "category": "perspective",
            "title": "第三人称限知",
            "description": "紧贴主角",
            "priority": "must",
        }
    ]
    bible.put_section(pid, "notes", notes)

    ctx = builder.build(project, "ch_001", "开写")
    assert "第三人称限知" in ctx["style_rules"]
    assert "必须/视角" in ctx["style_rules"]
    assert ctx["style_notes"] == "冷峻悬疑"
