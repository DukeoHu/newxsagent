from xsagent.domain.narrative.normalize import (
    normalize_volume_threads,
    suggested_thread_ids,
    volume_has_usable_threads,
)


def test_normalize_empty_threads_by_genre():
    volume = {"volume_id": "vol_01", "chapter_range": [1, 30], "threads": []}
    threads = normalize_volume_threads(volume, genre="校园重生甜宠")
    ids = [item["id"] for item in threads]
    assert "main" in ids
    assert "romance" in ids
    assert all(item.get("stages") for item in threads)
    assert all(item.get("milestones") for item in threads)


def test_normalize_enriches_incomplete_llm_thread():
    volume = {
        "chapter_range": [1, 20],
        "threads": [{"id": "main", "label": "主线", "milestones": [], "stages": []}],
    }
    threads = normalize_volume_threads(volume, genre="都市")
    main = next(item for item in threads if item["id"] == "main")
    assert len(main["stages"]) >= 3
    assert len(main["milestones"]) >= 2


def test_suggested_thread_ids_for_mystery():
    ids = suggested_thread_ids("悬疑科幻")
    assert "main" in ids
    assert "mystery" in ids


def test_volume_has_usable_threads():
    assert not volume_has_usable_threads({"threads": []})
    assert volume_has_usable_threads({"threads": [{"id": "main"}]})
