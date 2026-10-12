"""将 LLM 产出的叙事线程规范化并补全台阶。"""

from __future__ import annotations

from typing import Any

from xsagent.domain.narrative.thread_progress import DEFAULT_THREAD_STAGES

# 题材关键词 → 建议线程 id
_GENRE_THREAD_HINTS: dict[str, list[str]] = {
    "甜": ["main", "romance", "academic"],
    "恋爱": ["main", "romance"],
    "校园": ["main", "romance", "academic"],
    "重生": ["main", "romance", "mystery"],
    "悬疑": ["main", "mystery"],
    "科幻": ["main", "mystery", "academic"],
    "修仙": ["main", "mystery"],
    "玄幻": ["main", "mystery"],
    "都市": ["main", "romance", "academic"],
    "职场": ["main", "academic", "romance"],
}


def suggested_thread_ids(genre: str) -> list[str]:
    text = genre or ""
    ids: list[str] = ["main"]
    for key, thread_ids in _GENRE_THREAD_HINTS.items():
        if key in text:
            for tid in thread_ids:
                if tid not in ids:
                    ids.append(tid)
    if len(ids) == 1:
        ids.extend(["romance", "academic", "mystery"])
    return ids


def _default_stages(thread_id: str) -> list[dict[str, Any]]:
    defaults = DEFAULT_THREAD_STAGES.get(thread_id, DEFAULT_THREAD_STAGES["main"])
    return [dict(item) for item in defaults]


def _default_priority(thread_id: str) -> str:
    if thread_id == "main":
        return "high_early"
    if thread_id in {"romance", "mystery"}:
        return "low_early_high_mid"
    return "steady"


def _default_label(thread_id: str) -> str:
    labels = {
        "main": "主线",
        "romance": "感情线",
        "academic": "学业线",
        "mystery": "悬疑线",
    }
    return labels.get(thread_id, thread_id)


def _default_milestones(
    thread_id: str, *, volume_start: int, volume_end: int
) -> list[dict[str, Any]]:
    span = max(1, volume_end - volume_start + 1)
    early = volume_start
    mid = volume_start + max(1, span // 3)
    late = volume_start + max(2, (span * 2) // 3)
    templates: dict[str, list[dict[str, Any]]] = {
        "main": [
            {"id": "m1", "summary": "确认处境与主线目标", "earliest_chapter": early},
            {"id": "m2", "summary": "主线初次冲突", "earliest_chapter": mid},
            {"id": "m3", "summary": "主线阶段性兑现", "earliest_chapter": late},
        ],
        "romance": [
            {"id": "r1", "summary": "远观印象", "earliest_chapter": early},
            {"id": "r2", "summary": "间接关联", "earliest_chapter": mid},
            {"id": "r3", "summary": "首次有效互动", "earliest_chapter": late},
        ],
        "academic": [
            {"id": "a1", "summary": "学业基线展示", "earliest_chapter": early + 1},
            {"id": "a2", "summary": "小胜或认可", "earliest_chapter": mid},
        ],
        "mystery": [
            {"id": "y1", "summary": "轻微违和", "earliest_chapter": early + 1},
            {"id": "y2", "summary": "可验证线索", "earliest_chapter": mid},
        ],
    }
    return [dict(item) for item in templates.get(thread_id, templates["main"])]


def _normalize_one_thread(
    raw: dict[str, Any],
    *,
    volume_start: int,
    volume_end: int,
) -> dict[str, Any]:
    thread_id = str(raw.get("id") or "main").strip() or "main"
    stages = raw.get("stages")
    if not isinstance(stages, list) or not stages:
        stages = _default_stages(thread_id)
    else:
        cleaned_stages: list[dict[str, Any]] = []
        for item in stages:
            if not isinstance(item, dict):
                continue
            cleaned_stages.append(
                {
                    "level": int(item.get("level", 0)),
                    "id": str(item.get("id") or f"stage_{item.get('level', 0)}"),
                    "label": str(item.get("label") or item.get("id") or ""),
                    "ceiling": str(item.get("ceiling") or "遵守本台阶上限，勿提前兑现"),
                }
            )
        stages = cleaned_stages or _default_stages(thread_id)

    milestones = raw.get("milestones")
    if not isinstance(milestones, list) or not milestones:
        milestones = _default_milestones(
            thread_id, volume_start=volume_start, volume_end=volume_end
        )
    else:
        cleaned_ms: list[dict[str, Any]] = []
        for item in milestones:
            if not isinstance(item, dict):
                continue
            cleaned_ms.append(
                {
                    "id": str(item.get("id") or "ms"),
                    "summary": str(item.get("summary") or ""),
                    "earliest_chapter": int(
                        item.get("earliest_chapter", volume_start)
                    ),
                }
            )
        milestones = cleaned_ms or _default_milestones(
            thread_id, volume_start=volume_start, volume_end=volume_end
        )

    return {
        "id": thread_id,
        "label": str(raw.get("label") or _default_label(thread_id)),
        "priority_curve": str(raw.get("priority_curve") or _default_priority(thread_id)),
        "milestones": milestones,
        "stages": stages,
    }


def normalize_volume_threads(
    volume: dict[str, Any],
    *,
    genre: str = "",
    fill_if_empty: bool = True,
) -> list[dict[str, Any]]:
    """规范化 volume.threads；若为空则按题材填充默认骨架（仍可被 LLM 覆盖）。"""
    chapter_range = volume.get("chapter_range") or [1, 30]
    start = int(chapter_range[0]) if len(chapter_range) >= 1 else 1
    end = int(chapter_range[1]) if len(chapter_range) >= 2 else start + 29

    raw_threads = volume.get("threads")
    by_id: dict[str, dict[str, Any]] = {}
    if isinstance(raw_threads, list):
        for item in raw_threads:
            if isinstance(item, dict) and item.get("id"):
                normalized = _normalize_one_thread(
                    item, volume_start=start, volume_end=end
                )
                by_id[normalized["id"]] = normalized

    if not by_id and fill_if_empty:
        for thread_id in suggested_thread_ids(genre):
            by_id[thread_id] = _normalize_one_thread(
                {"id": thread_id},
                volume_start=start,
                volume_end=end,
            )
    elif "main" not in by_id:
        by_id["main"] = _normalize_one_thread(
            {"id": "main"},
            volume_start=start,
            volume_end=end,
        )

    # main 优先
    ordered: list[dict[str, Any]] = []
    if "main" in by_id:
        ordered.append(by_id.pop("main"))
    ordered.extend(by_id.values())
    return ordered


def volume_has_usable_threads(volume: dict[str, Any]) -> bool:
    threads = volume.get("threads")
    return isinstance(threads, list) and any(
        isinstance(item, dict) and item.get("id") for item in threads
    )
