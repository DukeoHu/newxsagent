import pytest

from xsagent.agents.explore import ExploreAgent
from xsagent.llm.simulator import SimulatorProvider


@pytest.mark.asyncio
async def test_explore_agent_returns_distinct_options():
    agent = ExploreAgent(SimulatorProvider())
    options = await agent.propose(
        chapter_id="ch_001",
        prompt="主角发现新的线索",
        count=3,
        context={"hard_constraints": "不得揭晓终局", "chapter_mandate": "推进主线"},
    )
    assert len(options) == 3
    titles = {item.title for item in options}
    assert len(titles) == 3
    winner, reason = await agent.judge(options)
    assert winner in {item.option_id for item in options}
    assert reason


@pytest.mark.asyncio
async def test_explore_agent_falls_back_when_llm_returns_garbage():
    class Broken:
        async def generate(self, request):
            return "not-json"

        async def stream(self, request):
            yield "x"

    agent = ExploreAgent(Broken())
    options = await agent.propose(chapter_id="ch_002", prompt="试探", count=2)
    assert len(options) == 2
    assert options[0].beats
