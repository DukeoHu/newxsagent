from xsagent.domain.common.scope import volume_scope_context
from xsagent.domain.narrative.mandate import ChapterMandateBuilder
from xsagent.domain.narrative.thread_progress import parse_thread_ledgers


VOLUME = {
    "volume_id": "vol_01",
    "title": "第一卷",
    "chapter_range": [1, 32],
    "stage_goal": "初步建立与女主的互动模式",
    "opening_focus": "重生适应、日常违和、远观女主",
    "opening_knowledge": ["底层日常", "轻微违和感"],
    "allowed_knowledge": ["学业竞争", "互动模式"],
    "forbidden_reveals": ["告白", "确立关系", "真相揭晓"],
    "threads": [
        {
            "id": "main",
            "label": "主线",
            "priority_curve": "high_early",
            "milestones": [{"id": "m1", "summary": "确认重生", "earliest_chapter": 1}],
        },
        {
            "id": "romance",
            "label": "感情线",
            "priority_curve": "low_early_high_mid",
            "milestones": [
                {"id": "r1", "summary": "远观印象", "earliest_chapter": 1},
                {"id": "r2", "summary": "间接关联", "earliest_chapter": 8},
            ],
        },
        {
            "id": "academic",
            "label": "学业线",
            "priority_curve": "steady",
            "milestones": [{"id": "a1", "summary": "课堂小胜", "earliest_chapter": 6}],
        },
        {
            "id": "mystery",
            "label": "悬疑线",
            "priority_curve": "low_early_high_mid",
            "milestones": [{"id": "y1", "summary": "违和细节", "earliest_chapter": 2}],
        },
    ],
}


def test_opening_scope_hides_stage_goal():
    scope = volume_scope_context(VOLUME, chapter_no=2)
    assert scope["tier"] == "opening"
    assert "stage_goal" not in scope
    assert scope["opening_focus"] == "重生适应、日常违和、远观女主"
    assert "arc_guidance" not in scope


def test_late_scope_includes_stage_goal():
    scope = volume_scope_context(VOLUME, chapter_no=28)
    assert scope["tier"] == "late"
    assert scope["stage_goal"] == "初步建立与女主的互动模式"


def test_mandate_dormant_threads_in_opening():
    builder = ChapterMandateBuilder()
    mandate = builder.build(
        chapter_id="ch_001",
        chapter_no=1,
        volume=VOLUME,
        plot_section={"thread_ledgers": {}},
        characters_section={
            "characters": [
                {"id": "char_lin", "name": "林", "role": "主角"},
                {"id": "char_su", "name": "苏", "role": "女主"},
            ]
        },
    )
    assert mandate.tier == "opening"
    assert mandate.chapter_role == "setup"
    assert mandate.primary_thread == "main"
    assert "romance" in mandate.dormant_threads
    assert "mystery" in mandate.dormant_threads
    assert "academic" in mandate.dormant_threads
    assert "禁止" in mandate.thread_ceilings["romance"]
    assert "休眠" in mandate.thread_ceilings["mystery"]
    assert "互动模式" not in mandate.narrative_goal


def test_mandate_allows_romance_progress_in_mid():
    builder = ChapterMandateBuilder()
    mandate = builder.build(
        chapter_id="ch_020",
        chapter_no=20,
        volume=VOLUME,
        plot_section={
            "thread_ledgers": {
                "romance": {
                    "progress_level": 2,
                    "current_stage": "indirect_link",
                    "last_progress_chapter": "ch_015",
                    "pair": ["char_lin", "char_su"],
                }
            }
        },
        characters_section={
            "characters": [
                {"id": "char_lin", "role": "主角"},
                {"id": "char_su", "role": "女主"},
            ]
        },
    )
    assert mandate.tier == "mid"
    assert "romance" not in mandate.dormant_threads
    assert "互动" in mandate.narrative_goal
    assert mandate.thread_states["romance"]["progress_level"] == 2


def test_legacy_relationship_ledger_maps_to_romance_thread():
    plot = {
        "relationship_ledger": {
            "pairs": [
                {
                    "chars": ["char_lin", "char_su"],
                    "intimacy_level": 1,
                    "current_stage": "distant_awareness",
                    "last_interaction_chapter": "ch_005",
                }
            ]
        }
    }
    ledgers = parse_thread_ledgers(plot)
    assert ledgers["romance"]["progress_level"] == 1
    assert ledgers["romance"]["current_stage"] == "distant_awareness"


def test_academic_thread_has_ceiling():
    builder = ChapterMandateBuilder()
    mandate = builder.build(
        chapter_id="ch_008",
        chapter_no=8,
        volume=VOLUME,
        plot_section={"thread_ledgers": {"academic": {"progress_level": 0}}},
    )
    assert "academic" in mandate.thread_ceilings
    assert "竞赛" in mandate.thread_ceilings["academic"] or "成绩" in mandate.thread_ceilings["academic"]
