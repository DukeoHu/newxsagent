"""兼容旧引用：关系进度逻辑已迁移至 thread_progress。"""

from typing import Any

from xsagent.domain.narrative.thread_progress import (
    DEFAULT_THREAD_STAGES,
    ceiling_for_level,
    default_romance_pair,
    parse_thread_ledgers,
    stage_id_for_level,
    thread_state,
)

INTIMACY_STAGES = DEFAULT_THREAD_STAGES["romance"]


def intimacy_ceiling(level: int) -> str:
    from xsagent.domain.narrative.models import NarrativeThread

    return ceiling_for_level(NarrativeThread(id="romance", label="感情线"), level)


def stage_for_level(level: int) -> str:
    from xsagent.domain.narrative.models import NarrativeThread

    return stage_id_for_level(NarrativeThread(id="romance", label="感情线"), level)


def parse_relationship_ledger(plot_section: dict[str, Any]) -> dict[str, Any]:
    ledgers = parse_thread_ledgers(plot_section)
    romance = ledgers.get("romance", {})
    pair = romance.get("pair") or romance.get("chars") or []
    return {
        "pairs": [
            {
                "chars": pair,
                "intimacy_level": int(romance.get("progress_level", 0)),
                "current_stage": romance.get("current_stage", "unaware"),
                "last_interaction_chapter": romance.get("last_progress_chapter"),
                "interaction_history": romance.get("history", []),
            }
        ]
    }


def primary_pair_state(
    ledger: dict[str, Any],
    *,
    default_chars: list[str] | None = None,
) -> dict[str, Any]:
    pairs = ledger.get("pairs", [])
    if pairs and isinstance(pairs[0], dict):
        return pairs[0]
    return {
        "chars": default_chars or [],
        "intimacy_level": 0,
        "current_stage": "unaware",
        "last_interaction_chapter": None,
        "interaction_history": [],
    }
