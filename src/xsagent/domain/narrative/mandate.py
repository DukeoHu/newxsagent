"""本章写作指令（Chapter Mandate）调度器。"""

from __future__ import annotations

from typing import Any

from xsagent.domain.common.scope import chapter_tier_in_volume
from xsagent.domain.narrative.models import ChapterMandate, ChapterRole, NarrativeThread
from xsagent.domain.narrative.thread_progress import (
    default_romance_pair,
    parse_thread_ledgers,
    thread_state,
)

DEFAULT_THREADS: list[dict[str, Any]] = [
    {
        "id": "main",
        "label": "主线",
        "priority_curve": "high_early",
        "milestones": [],
    },
    {
        "id": "romance",
        "label": "感情线",
        "priority_curve": "low_early_high_mid",
        "milestones": [],
    },
    {
        "id": "academic",
        "label": "学业线",
        "priority_curve": "steady",
        "milestones": [],
    },
    {
        "id": "mystery",
        "label": "悬疑线",
        "priority_curve": "low_early_high_mid",
        "milestones": [],
    },
]


def _derive_opening_focus(volume: dict[str, Any]) -> str:
    explicit = str(volume.get("opening_focus", "")).strip()
    if explicit:
        return explicit
    opening = volume.get("opening_knowledge", [])
    if isinstance(opening, list) and opening:
        return "、".join(str(item) for item in opening[:3])
    return "卷初慢热：日常、人设、轻微违和；非主推进线程本章尽量不推进"


def _threads_from_volume(volume: dict[str, Any] | None) -> list[NarrativeThread]:
    if not volume:
        return [NarrativeThread.model_validate(item) for item in DEFAULT_THREADS]
    raw = volume.get("threads")
    if isinstance(raw, list) and raw:
        return [NarrativeThread.model_validate(item) for item in raw]
    return [NarrativeThread.model_validate(item) for item in DEFAULT_THREADS]


def _chapter_role_for_tier(tier: str) -> ChapterRole:
    if tier == "opening":
        return "setup"
    if tier == "early":
        return "bridge"
    if tier == "mid":
        return "escalation"
    return "payoff"


def _thread_active(thread: NarrativeThread, tier: str) -> bool:
    curve = thread.priority_curve
    if curve == "high_early":
        return tier in {"opening", "early", "mid", "late"}
    if curve == "low_early_high_mid":
        return tier in {"mid", "late"}
    return tier in {"early", "mid", "late"}


def _thread_dormant(thread: NarrativeThread, tier: str) -> bool:
    if thread.priority_curve == "low_early_high_mid" and tier in {"opening", "early"}:
        return True
    return not _thread_active(thread, tier)


def _eligible_milestones(thread: NarrativeThread, chapter_no: int) -> list[str]:
    targets: list[str] = []
    for milestone in thread.milestones:
        if chapter_no >= milestone.earliest_chapter:
            targets.append(f"{thread.label}:{milestone.summary}")
    return targets[:1]


def _narrative_goal(
    volume: dict[str, Any] | None,
    tier: str,
    primary_thread: NarrativeThread,
    *,
    dormant_threads: list[NarrativeThread],
) -> str:
    if tier in {"opening", "early"}:
        focus = _derive_opening_focus(volume or {})
        dormant_labels = "、".join(thread.label for thread in dormant_threads) or "无"
        return f"{focus}（主推进：{primary_thread.label}；休眠线程：{dormant_labels}）"
    stage_goal = str((volume or {}).get("stage_goal", "")).strip()
    if stage_goal and tier in {"mid", "late"}:
        return f"当前卷阶段目标：{stage_goal}（主推进：{primary_thread.label}）"
    return f"推进{primary_thread.label}，保持卷内节奏递进"


class ChapterMandateBuilder:
    def build(
        self,
        *,
        chapter_id: str,
        chapter_no: int,
        volume: dict[str, Any] | None,
        plot_section: dict[str, Any] | None = None,
        characters_section: dict[str, Any] | None = None,
    ) -> ChapterMandate:
        tier = "opening"
        if volume and isinstance(volume.get("chapter_range"), list) and len(volume["chapter_range"]) >= 2:
            start, end = int(volume["chapter_range"][0]), int(volume["chapter_range"][1])
            tier = chapter_tier_in_volume(start, end, chapter_no)

        threads = _threads_from_volume(volume)
        dormant_ids = [t.id for t in threads if _thread_dormant(t, tier)]
        dormant_threads = [t for t in threads if t.id in dormant_ids]
        active_threads = [t for t in threads if t.id not in dormant_ids]
        primary = active_threads[0] if active_threads else threads[0]

        plot_section = plot_section or {}
        characters = list((characters_section or {}).get("characters", []))
        ledgers = parse_thread_ledgers(plot_section)

        thread_states: dict[str, dict[str, Any]] = {}
        thread_ceilings: dict[str, str] = {}
        for thread in threads:
            state = thread_state(ledgers, thread)
            thread_states[thread.id] = state
            thread_ceilings[thread.id] = state["ceiling"]
            if thread.id in dormant_ids:
                thread_ceilings[thread.id] = (
                    f"本章休眠，不得推进；当前进度上限：{state['ceiling']}"
                )

        milestone_targets: list[str] = []
        for thread in active_threads:
            milestone_targets.extend(_eligible_milestones(thread, chapter_no))

        romance_state = thread_states.get("romance", {})
        pair_chars = romance_state.get("metadata", {}).get("pair") or default_romance_pair(characters)
        relationship_state = {
            "pair": pair_chars or [],
            "intimacy_level": romance_state.get("progress_level", 0),
            "current_stage": romance_state.get("current_stage", "unaware"),
            "last_interaction_chapter": romance_state.get("last_progress_chapter"),
        }

        return ChapterMandate(
            chapter_id=chapter_id,
            chapter_no=chapter_no,
            tier=tier,
            chapter_role=_chapter_role_for_tier(tier),
            primary_thread=primary.id,
            dormant_threads=dormant_ids,
            thread_ceilings=thread_ceilings,
            romance_ceiling=thread_ceilings.get("romance", ""),
            narrative_goal=_narrative_goal(
                volume,
                tier,
                primary,
                dormant_threads=dormant_threads,
            ),
            milestone_targets=milestone_targets,
            thread_states=thread_states,
            relationship_state=relationship_state,
        )

    def build_batch_json(
        self,
        chapter_ids: list[str],
        *,
        volume: dict[str, Any] | None,
        plot_section: dict[str, Any] | None = None,
        characters_section: dict[str, Any] | None = None,
        chapter_number_fn,
    ) -> str:
        import json

        mandates = {
            cid: self.build(
                chapter_id=cid,
                chapter_no=chapter_number_fn(cid),
                volume=volume,
                plot_section=plot_section,
                characters_section=characters_section,
            ).to_dict()
            for cid in chapter_ids
        }
        return json.dumps(mandates, ensure_ascii=False)
