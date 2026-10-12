"""分层信息边界：全书 → 卷 → 章位阶，控制可注入 prompt 的知识范围。"""

from __future__ import annotations

import json
from typing import Any, Literal

Tier = Literal["opening", "early", "mid", "late"]


def chapter_number(chapter_id: str) -> int:
    from xsagent.domain.common.spoiler import chapter_number as _chapter_number

    return _chapter_number(chapter_id)


def find_volume_for_chapter(
    volumes: list[dict[str, Any]], chapter_no: int
) -> dict[str, Any] | None:
    for volume in volumes:
        chapter_range = volume.get("chapter_range")
        if not isinstance(chapter_range, list) or len(chapter_range) < 2:
            continue
        start, end = int(chapter_range[0]), int(chapter_range[1])
        if start <= chapter_no <= end:
            return volume
    return None


def chapter_tier_in_volume(
    volume_start: int, volume_end: int, chapter_no: int
) -> Tier:
    span = max(1, volume_end - volume_start + 1)
    position = max(1, chapter_no - volume_start + 1)
    opening_cutoff = max(3, span // 10)
    early_cutoff = max(opening_cutoff + 1, span // 3)
    mid_cutoff = max(early_cutoff + 1, (span * 2) // 3)

    if position <= opening_cutoff:
        return "opening"
    if position <= early_cutoff:
        return "early"
    if position <= mid_cutoff:
        return "mid"
    return "late"


def _derive_opening_focus(volume: dict[str, Any]) -> str:
    explicit = str(volume.get("opening_focus", "")).strip()
    if explicit:
        return explicit
    opening = volume.get("opening_knowledge", [])
    if isinstance(opening, list) and opening:
        return "、".join(str(item) for item in opening[:3])
    return ""


def _arc_phases_for_chapter(volume: dict[str, Any], chapter_no: int) -> list[dict[str, Any]]:
    phases = volume.get("arc_phases")
    if not isinstance(phases, list) or not phases:
        return []
    matched: list[dict[str, Any]] = []
    for phase in phases:
        if not isinstance(phase, dict):
            continue
        chapter_range = phase.get("chapter_range")
        if (
            isinstance(chapter_range, list)
            and len(chapter_range) >= 2
            and int(chapter_range[0]) <= chapter_no <= int(chapter_range[1])
        ):
            matched.append(phase)
    return matched


def volume_scope_context(volume: dict[str, Any], chapter_no: int) -> dict[str, Any]:
    """构造当前章节可见的卷级信息边界（不含后续卷/终局）。"""
    chapter_range = volume.get("chapter_range") or []
    if len(chapter_range) < 2:
        return {"volume_id": volume.get("volume_id"), "tier": "opening"}

    start, end = int(chapter_range[0]), int(chapter_range[1])
    tier = chapter_tier_in_volume(start, end, chapter_no)
    position = chapter_no - start + 1
    span = end - start + 1

    scope: dict[str, Any] = {
        "volume_id": volume.get("volume_id"),
        "title": volume.get("title", ""),
        "chapter_position": f"本卷第{position}/{span}章（全书第{chapter_no}章）",
        "tier": tier,
        "forbidden_reveals": list(volume.get("forbidden_reveals", [])),
    }

    opening_focus = _derive_opening_focus(volume)
    if tier in {"opening", "early"}:
        if opening_focus:
            scope["opening_focus"] = opening_focus
    else:
        stage_goal = str(volume.get("stage_goal", "")).strip()
        if stage_goal:
            scope["stage_goal"] = stage_goal

    opening_knowledge = list(volume.get("opening_knowledge", []))
    allowed_knowledge = list(volume.get("allowed_knowledge", []))
    if tier == "opening" and opening_knowledge:
        scope["allowed_knowledge"] = opening_knowledge
        scope["mode"] = "卷初开篇：仅允许日常、人物状态、轻微违和感；禁止进入卷内高潮与关键揭晓"
    elif tier == "opening":
        scope["allowed_knowledge"] = allowed_knowledge[:3]
        scope["mode"] = "卷初开篇：仅允许少量已声明信息，禁止提前推进卷内弧线高潮"
    else:
        scope["allowed_knowledge"] = allowed_knowledge

    if tier in {"mid", "late"}:
        scope["knowledge_ceiling"] = volume.get("knowledge_ceiling", "")
        scope["arc_guidance"] = volume.get("arcs", [])
    elif tier == "early":
        phases = _arc_phases_for_chapter(volume, chapter_no)
        if phases:
            scope["arc_guidance"] = phases
        else:
            arcs = volume.get("arcs", [])
            if isinstance(arcs, list) and arcs:
                scope["arc_guidance"] = [arcs[0]]

    plants: list[dict[str, str]] = []
    for item in volume.get("foreshadowing_plants", []):
        if not isinstance(item, dict):
            continue
        earliest = int(item.get("earliest_chapter", start))
        latest = int(item.get("latest_chapter", end))
        if earliest <= chapter_no <= latest:
            plants.append(
                {
                    "hook": str(item.get("hook", "")),
                    "plant_hint": str(item.get("plant_hint", "")),
                }
            )
    if plants:
        scope["foreshadowing_to_plant_now"] = plants

    return scope


def minimal_bible_for_chapter(
    sections: dict[str, dict[str, Any]],
    *,
    tier: Tier,
) -> dict[str, dict[str, Any]]:
    """章节级 Bible：只保留写作当下需要的公开设定。"""
    result: dict[str, dict[str, Any]] = {}

    characters = sections.get("characters", {})
    if characters:
        chars = characters.get("characters", [])
        if isinstance(chars, list):
            public_chars = []
            for char in chars:
                if not isinstance(char, dict):
                    continue
                public_chars.append(
                    {
                        "id": char.get("id"),
                        "name": char.get("name"),
                        "role": char.get("role"),
                        "current_state": char.get("current_state"),
                        **(
                            {"goal": char.get("goal")}
                            if tier in {"mid", "late"}
                            else {}
                        ),
                    }
                )
            result["characters"] = {"characters": public_chars}

    world = sections.get("world", {})
    if world:
        result["world"] = {
            "rules": world.get("rules", [])[:4] if tier == "opening" else world.get("rules", []),
            "locations": world.get("locations", [])[:3] if tier == "opening" else world.get("locations", []),
        }

    notes = sections.get("notes", {})
    if notes and (notes.get("style_notes") or notes.get("style_rules")):
        notes_out: dict[str, Any] = {}
        if notes.get("style_notes"):
            notes_out["style_notes"] = notes.get("style_notes", "")
        if notes.get("style_rules"):
            notes_out["style_rules"] = notes.get("style_rules", [])
        result["notes"] = notes_out

    # plot / timeline / spoiler_vault 默认不注入章节蓝图与开篇写作
    return result


def scoped_context_for_chapter(
    *,
    bible_sections: dict[str, dict[str, Any]],
    volume: dict[str, Any] | None,
    chapter_no: int,
    master_acts: list[dict[str, Any]] | None = None,
) -> str:
    """合并卷级边界 + 最小 Bible，供蓝图/写作 prompt 使用。"""
    from xsagent.domain.common.spoiler import filter_master_for_chapter, spoiler_safe_bible_sections

    volume_ctx = volume_scope_context(volume, chapter_no) if volume else {}
    tier = volume_ctx.get("tier", "opening")

    safe_sections = spoiler_safe_bible_sections(
        bible_sections,
        chapter_no,
        master_acts=master_acts,
        early_threshold=10 if tier == "opening" else 30,
    )
    minimal = minimal_bible_for_chapter(safe_sections, tier=tier)

    master_slice: dict[str, Any] = {}
    if master_acts:
        master_slice = filter_master_for_chapter({"acts": master_acts}, chapter_no)

    payload = {
        "volume_boundary": volume_ctx,
        "public_bible": minimal,
        "current_act": master_slice.get("acts", []),
    }
    return json.dumps(payload, ensure_ascii=False)


def volume_scope_text(volume: dict[str, Any], chapter_no: int) -> str:
    return json.dumps(volume_scope_context(volume, chapter_no), ensure_ascii=False)
