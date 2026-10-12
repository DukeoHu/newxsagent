"""按章节位阶过滤剧透，避免早期蓝图/正文提前揭晓伏笔。"""

from __future__ import annotations

import json
import re
from typing import Any

from xsagent.agents.prompts.outline import (
    NARRATIVE_GOAL_CURRENT_ACT,
    NARRATIVE_GOAL_DEFAULT,
    NARRATIVE_GOAL_EARLY_STAGE,
    NARRATIVE_GOAL_FALLBACK_SUMMARY,
    NARRATIVE_GOAL_TOWARD_ENDING,
    SPOILER_GUARD_BASE_RULES,
    SPOILER_GUARD_EARLY_RULE,
    SPOILER_GUARD_HEADER,
    SPOILER_GUARD_OPENING_RULE,
    SPOILER_GUARD_THREAD_RULE,
)

_LATER_VOLUME_MARKERS = ("第二卷", "第三卷", "第四卷", "第五卷", "终局", "全书终")


def chapter_number(chapter_id: str) -> int:
    match = re.match(r"ch_(\d+)", chapter_id)
    return int(match.group(1)) if match else 0


def strip_future_author_notes(author_notes: str, chapter_no: int, *, early_threshold: int = 30) -> str:
    text = author_notes.strip()
    if not text or chapter_no > early_threshold:
        return text

    for tag in ("【剧透库】", "【伏笔库】", "【全书结构】"):
        idx = text.find(tag)
        if idx >= 0:
            text = text[:idx].strip()

    earliest: int | None = None
    for marker in _LATER_VOLUME_MARKERS:
        idx = text.find(marker)
        if idx >= 0 and (earliest is None or idx < earliest):
            earliest = idx

    if earliest is not None and earliest > 0:
        text = text[:earliest].strip()

    return text


def filter_plot_acts(
    acts: list[dict[str, Any]],
    chapter_no: int,
    master_acts: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if master_acts:
        past: list[dict[str, Any]] = []
        for act in master_acts:
            chapter_range = act.get("chapter_range")
            if not isinstance(chapter_range, list) or len(chapter_range) < 2:
                continue
            start, end = int(chapter_range[0]), int(chapter_range[1])
            if start <= chapter_no <= end:
                return [act]
            if end < chapter_no:
                past.append(
                    {
                        "id": act.get("id"),
                        "title": act.get("title"),
                        "summary": act.get("summary"),
                        "chapter_range": chapter_range,
                    }
                )
        if past:
            return past[-1:]
        return master_acts[:1]

    if not acts:
        return []
    if chapter_no <= 30:
        return [acts[0]]
    if chapter_no <= 100 and len(acts) >= 2:
        return acts[:2]
    return acts


def filter_foreshadowing(
    foreshadowing: list[dict[str, Any]], chapter_no: int
) -> list[dict[str, Any]]:
    plantable: list[dict[str, Any]] = []
    for item in foreshadowing:
        reveal_after = int(item.get("reveal_after_chapter", 9999))
        plant_from = int(item.get("plant_from_chapter", 1))
        if plant_from <= chapter_no < reveal_after:
            plantable.append(
                {
                    "id": item.get("id"),
                    "hook": item.get("hook"),
                    "plant_hint": item.get("plant_hint"),
                }
            )
    return plantable


def spoiler_safe_bible_sections(
    sections: dict[str, dict[str, Any]],
    chapter_no: int,
    *,
    master_acts: list[dict[str, Any]] | None = None,
    early_threshold: int = 30,
) -> dict[str, dict[str, Any]]:
    filtered: dict[str, dict[str, Any]] = {}
    for name, data in sections.items():
        if name == "notes":
            notes = dict(data)
            notes.pop("spoiler_vault", None)
            notes["author_notes"] = strip_future_author_notes(
                str(notes.get("author_notes", "")),
                chapter_no,
                early_threshold=early_threshold,
            )
            filtered[name] = notes
            continue

        if name == "plot":
            plot = dict(data)
            plot["acts"] = filter_plot_acts(
                list(plot.get("acts", [])),
                chapter_no,
                master_acts,
            )
            foreshadowing = plot.get("foreshadowing")
            if isinstance(foreshadowing, list) and foreshadowing:
                plot["foreshadowing"] = filter_foreshadowing(foreshadowing, chapter_no)
            else:
                plot.pop("foreshadowing", None)
            filtered[name] = plot
            continue

        if name == "timeline":
            timeline = dict(data)
            events = timeline.get("events", [])
            if isinstance(events, list):
                timeline["events"] = [
                    event
                    for event in events
                    if chapter_number(str(event.get("chapter", "ch_999"))) <= chapter_no
                ]
            filtered[name] = timeline
            continue

        filtered[name] = data
    return filtered


def bible_summary_text(sections: dict[str, dict[str, Any]]) -> str:
    parts: list[str] = []
    for section in sorted(sections.keys()):
        data = sections[section]
        compact = {key: value for key, value in data.items() if key != "locked_fields"}
        parts.append(f"[{section}] {json.dumps(compact, ensure_ascii=False)}")
    return "\n".join(parts)


def _opening_act_summary(act: dict[str, Any], chapter_no: int) -> str:
    summary = str(act.get("summary", "")).strip()
    if not summary:
        return ""
    chapter_range = act.get("chapter_range")
    if isinstance(chapter_range, list) and len(chapter_range) >= 2:
        start = int(chapter_range[0])
        if chapter_no <= start + 5:
            for sep in ("，", ",", "；", ";", "、"):
                if sep in summary:
                    return summary.split(sep)[0].strip()
            if len(summary) > 48:
                return summary[:48].rstrip() + "…"
    return summary


def filter_master_for_chapter(master: dict[str, Any], chapter_no: int) -> dict[str, Any]:
    filtered = dict(master)
    acts = list(master.get("acts", []))
    relevant: list[dict[str, Any]] = []
    for act in acts:
        chapter_range = act.get("chapter_range")
        if isinstance(chapter_range, list) and len(chapter_range) >= 2:
            start, end = int(chapter_range[0]), int(chapter_range[1])
            if end < chapter_no:
                relevant.append(
                    {
                        "id": act.get("id"),
                        "title": act.get("title"),
                        "summary": act.get("summary"),
                        "chapter_range": chapter_range,
                    }
                )
            elif start <= chapter_no <= end:
                trimmed = dict(act)
                trimmed["summary"] = _opening_act_summary(act, chapter_no)
                relevant.append(trimmed)
                break
        elif chapter_no <= 30 and not relevant:
            relevant.append(act)
            break

    filtered["acts"] = relevant or (acts[:1] if acts else [])
    if chapter_no <= 50:
        filtered.pop("ending_goal", None)
    return filtered


def narrative_goal_for_chapter(
    master: dict[str, Any],
    chapter_no: int,
    *,
    total_chapters: int = 0,
) -> str:
    acts = list(master.get("acts", []))
    for act in acts:
        chapter_range = act.get("chapter_range")
        if isinstance(chapter_range, list) and len(chapter_range) >= 2:
            start, end = int(chapter_range[0]), int(chapter_range[1])
            if start <= chapter_no <= end:
                return NARRATIVE_GOAL_CURRENT_ACT.format(
                    start=start,
                    end=end,
                    summary=act.get("summary", ""),
                )

    early_cutoff = max(30, (total_chapters or 100) // 5)
    if chapter_no <= early_cutoff and acts:
        first = acts[0]
        return NARRATIVE_GOAL_EARLY_STAGE.format(
            summary=first.get("summary", NARRATIVE_GOAL_FALLBACK_SUMMARY),
        )

    ending_goal = str(master.get("ending_goal", "")).strip()
    if ending_goal and chapter_no > early_cutoff:
        return NARRATIVE_GOAL_TOWARD_ENDING.format(ending_goal=ending_goal)
    return NARRATIVE_GOAL_DEFAULT


def spoiler_guard_for_chapter(chapter_no: int, *, total_chapters: int = 0) -> str:
    total = total_chapters or 100
    opening = chapter_no <= 5
    early = chapter_no <= max(10, total // 10)

    lines = [SPOILER_GUARD_HEADER, *SPOILER_GUARD_BASE_RULES]
    if opening:
        lines.append(SPOILER_GUARD_OPENING_RULE)
    if early:
        lines.append(SPOILER_GUARD_EARLY_RULE)
    if opening or early:
        lines.append(SPOILER_GUARD_THREAD_RULE)
    return "\n".join(lines)
