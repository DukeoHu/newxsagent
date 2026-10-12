from xsagent.domain.narrative.hard_constraints import (
    hard_constraints_from_mandate,
    hard_constraints_prompt_text,
    scrub_beats_against_hard_constraints,
)
from xsagent.domain.narrative.mandate import ChapterMandateBuilder
from xsagent.domain.narrative.models import ChapterMandate


def test_hard_constraints_from_mandate():
    mandate = ChapterMandate(
        chapter_id="ch_001",
        chapter_no=1,
        tier="opening",
        chapter_role="setup",
        primary_thread="main",
        dormant_threads=["romance", "mystery"],
        thread_ceilings={"romance": "仅可远观，不可互动"},
        romance_ceiling="仅可远观，不可互动",
        narrative_goal="适应重生日常",
        milestone_targets=["m1"],
    )
    hard = hard_constraints_from_mandate(mandate)
    assert hard["primary_thread"] == "main"
    assert "romance" in hard["dormant_threads"]
    text = hard_constraints_prompt_text(hard)
    assert "休眠线程" in text
    assert "romance" in text


def test_scrub_beats_dormant_romance():
    hard = {
        "dormant_threads": ["romance"],
        "primary_thread": "main",
    }
    beats = [
        "适应校园日常",
        "主动搭话女主并约独处",
        "章末留下一丝违和感",
    ]
    scrubbed, conflicts = scrub_beats_against_hard_constraints(beats, hard)
    assert any("不可" in b or "远观" in b or "不推进" in b for b in scrubbed)
    assert len(conflicts) >= 1
    assert "适应校园日常" in scrubbed


def test_opening_normalize_persists_hard_constraints_shape():
    builder = ChapterMandateBuilder()
    volume = {
        "volume_id": "vol_01",
        "title": "第一卷",
        "chapter_range": [1, 32],
        "stage_goal": "初步建立与女主的互动模式",
        "opening_focus": "重生适应",
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
                "milestones": [{"id": "r1", "summary": "远观", "earliest_chapter": 1}],
            },
        ],
    }
    mandate = builder.build(
        chapter_id="ch_001",
        chapter_no=1,
        volume=volume,
        plot_section={},
        characters_section={},
    )
    hard = hard_constraints_from_mandate(mandate)
    assert hard["tier"] == "opening"
    assert hard["primary_thread"] == "main"
