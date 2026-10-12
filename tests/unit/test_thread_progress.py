from xsagent.domain.narrative.thread_progress import (
    ceiling_for_level,
    parse_thread_ledgers,
    stages_for_thread,
)
from xsagent.domain.narrative.models import NarrativeThread


def test_default_stages_for_unknown_thread_falls_back_to_main():
    thread = NarrativeThread(id="custom_faction", label="势力线")
    stages = stages_for_thread(thread)
    assert len(stages) >= 3
    assert "冲突" in ceiling_for_level(thread, 2) or "目标" in ceiling_for_level(thread, 2)


def test_thread_ledgers_merge_legacy_relationship():
    plot = {
        "thread_ledgers": {"main": {"progress_level": 1, "current_stage": "adaptation"}},
        "relationship_ledger": {
            "pairs": [{"chars": ["a", "b"], "intimacy_level": 3, "current_stage": "cold_exchange"}]
        },
    }
    ledgers = parse_thread_ledgers(plot)
    assert ledgers["main"]["progress_level"] == 1
    assert ledgers["romance"]["progress_level"] == 3
