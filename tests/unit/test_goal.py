import json

import pytest

from xsagent.agents.goal import GoalVerifier
from xsagent.domain.quality.goal import MIN_CHAPTER_WORDS, word_count_gap
from xsagent.llm.base import LLMRequest, LLMTask
from xsagent.llm.simulator import SimulatorProvider


def test_word_count_gap_only_flags_stub_chapters():
    assert word_count_gap(10, 3000) is not None
    assert word_count_gap(MIN_CHAPTER_WORDS, 3000) is None
    assert word_count_gap(200, 3000) is None


@pytest.mark.asyncio
async def test_goal_verifier_passes_with_simulator():
    verifier = GoalVerifier(SimulatorProvider())
    verdict = await verifier.verify(
        chapter_id="ch_002",
        content="# 第二章\n\n林夕走进旧邮局。",
        word_count=80,
        words_per_chapter=3000,
        beats=["进入邮局"],
        dormant_threads=["romance"],
        forbidden_reveals=["终局真相"],
        hard_constraints="不得推进感情线",
        chapter_mandate="推进主线",
    )
    assert verdict.satisfied is True
    assert verdict.gaps == []


class _ShortCircuitLLM:
    async def generate(self, request: LLMRequest) -> str:
        assert request.task == LLMTask.GOAL_VERIFY
        return json.dumps(
            {
                "satisfied": True,
                "impossible": False,
                "gaps": [],
                "summary": "模型放行",
            },
            ensure_ascii=False,
        )

    async def stream(self, request: LLMRequest):
        yield await self.generate(request)


@pytest.mark.asyncio
async def test_goal_verifier_merges_deterministic_word_count_failure():
    verifier = GoalVerifier(_ShortCircuitLLM())
    verdict = await verifier.verify(
        chapter_id="ch_002",
        content="# 空\n\n。",
        word_count=2,
        words_per_chapter=3000,
        beats=[],
        dormant_threads=[],
        forbidden_reveals=[],
        hard_constraints="",
        chapter_mandate="",
    )
    assert verdict.satisfied is False
    assert any(gap.code == "word_count" for gap in verdict.gaps)
