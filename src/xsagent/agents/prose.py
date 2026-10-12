from collections.abc import AsyncIterator

from xsagent.agents.prompts import PROSE_SYSTEM, PROSE_TEMPLATE
from xsagent.llm.base import LLMProvider, LLMRequest, LLMTask


class ProseAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    def _prompt(self, context: dict) -> str:
        return PROSE_TEMPLATE.format(
            genre=context["genre"],
            name=context["name"],
            hard_constraints=context.get("hard_constraints", "（无硬约束）"),
            chapter_mandate=context["chapter_mandate"],
            author_notes=context.get("author_notes", "（无）"),
            volume_scope=context["volume_scope"],
            scoped_context=context["scoped_context"],
            chapter_blueprint=context["chapter_blueprint"],
            soft_constraints=context.get("soft_constraints", "（无）"),
            style_rules=context.get("style_rules", "（无结构化风格规则）"),
            style_notes=context["style_notes"],
            intervention_level=context["intervention_level"],
            session_checkpoint=context.get("session_checkpoint", "（尚无会话状态记录）"),
            recent_chapters_window=context["recent_chapters_window"],
            goal_feedback=context.get("goal_feedback", "（无）"),
            selected_plan=context.get("selected_plan", "（无）"),
            instruction=context["instruction"],
            words_per_chapter=context["words_per_chapter"],
        )

    async def generate(self, context: dict) -> str:
        request = LLMRequest(task=LLMTask.PROSE, system=PROSE_SYSTEM, prompt=self._prompt(context))
        return await self._llm.generate(request)

    async def stream(self, context: dict) -> AsyncIterator[str]:
        request = LLMRequest(task=LLMTask.PROSE, system=PROSE_SYSTEM, prompt=self._prompt(context))
        async for chunk in self._llm.stream(request):
            yield chunk
