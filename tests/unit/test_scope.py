"""卷级信息边界：分层披露。"""

from xsagent.domain.common.scope import (
    chapter_tier_in_volume,
    find_volume_for_chapter,
    volume_scope_context,
)


def test_opening_tier_uses_opening_knowledge_only():
    volume = {
        "volume_id": "vol_01",
        "title": "第一卷",
        "chapter_range": [1, 30],
        "stage_goal": "低调发育",
        "allowed_knowledge": ["零一觉醒", "零域追杀", "天网真相"],
        "opening_knowledge": ["底层黑客日常", "轻微违和感"],
        "forbidden_reveals": ["天网", "模拟世界"],
        "arcs": [{"summary": "唤醒零一并反杀零域"}],
    }
    scope = volume_scope_context(volume, chapter_no=2)
    assert scope["tier"] == "opening"
    assert scope["allowed_knowledge"] == ["底层黑客日常", "轻微违和感"]
    assert "stage_goal" not in scope
    assert "arc_guidance" not in scope


def test_late_tier_includes_arc_guidance():
    volume = {
        "volume_id": "vol_01",
        "chapter_range": [1, 30],
        "arcs": [{"summary": "卷末高潮"}],
        "allowed_knowledge": ["零一觉醒"],
        "forbidden_reveals": ["天网"],
    }
    scope = volume_scope_context(volume, chapter_no=25)
    assert scope["tier"] == "late"
    assert scope.get("arc_guidance")


def test_find_volume_for_chapter():
    volumes = [
        {"volume_id": "vol_01", "chapter_range": [1, 30]},
        {"volume_id": "vol_02", "chapter_range": [31, 60]},
    ]
    found = find_volume_for_chapter(volumes, 35)
    assert found is not None
    assert found["volume_id"] == "vol_02"


def test_chapter_tier_in_volume():
    assert chapter_tier_in_volume(1, 30, 2) == "opening"
    assert chapter_tier_in_volume(1, 30, 20) in {"mid", "late"}
