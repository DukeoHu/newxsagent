from xsagent.domain.common.spoiler import (
    filter_foreshadowing,
    filter_master_for_chapter,
    narrative_goal_for_chapter,
    spoiler_guard_for_chapter,
    spoiler_safe_bible_sections,
    strip_future_author_notes,
)


def test_strip_future_author_notes_removes_later_volumes():
    text = "第一卷铺垫。\n第二卷大战。\n第三卷终局真相。"
    result = strip_future_author_notes(text, chapter_no=3)
    assert "第二卷" not in result
    assert "第一卷铺垫" in result


def test_spoiler_safe_bible_sections_hides_vault_and_future_foreshadowing():
    sections = {
        "notes": {
            "style_notes": "悬疑",
            "author_notes": "开篇慢热",
            "spoiler_vault": "林一是天网备份",
        },
        "plot": {
            "acts": [
                {"id": "act_1", "title": "开篇", "summary": "低调发育"},
                {"id": "act_4", "title": "终局", "summary": "世界是模拟"},
            ],
            "foreshadowing": [
                {
                    "id": "fs_1",
                    "hook": "世界bug",
                    "plant_hint": "广告日期违和",
                    "plant_from_chapter": 1,
                    "reveal_after_chapter": 80,
                    "reveal_detail": "世界是被模拟的",
                }
            ],
        },
    }
    filtered = spoiler_safe_bible_sections(sections, chapter_no=3)
    assert "spoiler_vault" not in filtered["notes"]
    assert len(filtered["plot"]["acts"]) == 1
    assert filtered["plot"]["foreshadowing"][0]["hook"] == "世界bug"
    assert "reveal_detail" not in filtered["plot"]["foreshadowing"][0]


def test_filter_foreshadowing_excludes_revealed_items():
    items = [
        {
            "id": "fs_1",
            "hook": "监控痕迹",
            "plant_hint": "出租屋异常",
            "plant_from_chapter": 1,
            "reveal_after_chapter": 20,
        },
        {
            "id": "fs_2",
            "hook": "天网真相",
            "plant_hint": "不应出现",
            "plant_from_chapter": 1,
            "reveal_after_chapter": 5,
        },
    ]
    result = filter_foreshadowing(items, chapter_no=10)
    assert len(result) == 1
    assert result[0]["id"] == "fs_1"


def test_filter_master_for_chapter_hides_ending_goal_early():
    master = {
        "acts": [
            {"id": "act_1", "title": "第一幕", "summary": "铺垫", "chapter_range": [1, 30]},
            {"id": "act_4", "title": "终局", "summary": "真相揭晓", "chapter_range": [91, 100]},
        ],
        "ending_goal": "打破天网控制",
    }
    filtered = filter_master_for_chapter(master, chapter_no=2)
    assert len(filtered["acts"]) == 1
    assert filtered["acts"][0]["id"] == "act_1"
    assert "ending_goal" not in filtered


def test_narrative_goal_for_chapter_uses_current_act_not_ending():
    master = {
        "acts": [
            {"id": "act_1", "title": "第一幕", "summary": "低调发育", "chapter_range": [1, 30]},
        ],
        "ending_goal": "打破天网控制",
    }
    goal = narrative_goal_for_chapter(master, chapter_no=3, total_chapters=100)
    assert "低调发育" in goal
    assert "打破天网" not in goal


def test_filter_master_for_chapter_truncates_opening_summary():
    master = {
        "acts": [
            {
                "id": "act_1",
                "title": "第一幕",
                "summary": "低调发育，相遇互怼，情感破冰，高考告白",
                "chapter_range": [1, 30],
            },
        ],
        "ending_goal": "打破天网控制",
    }
    filtered = filter_master_for_chapter(master, chapter_no=2)
    assert filtered["acts"][0]["summary"] == "低调发育"


def test_spoiler_guard_for_opening_chapters():
    guard = spoiler_guard_for_chapter(2, total_chapters=100)
    assert "开篇前几章" in guard
    assert "线程节奏" in guard
