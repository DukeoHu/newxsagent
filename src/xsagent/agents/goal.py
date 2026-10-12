import json

from xsagent.agents.prompts.goal import GOAL_SYSTEM, GOAL_TEMPLATE
from xsagent.domain.quality.goal import GoalGap, GoalVerdict, word_count_gap
from xsagent.llm.base import LLMProvider, LLMRequest, LLMTask
from xsagent.llm.parse import parse_llm_json


class GoalVerifier:
    """独立于写作者的完成度验收；不参与正文生成。"""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def verify(
        self,
        *,
        chapter_id: str,
        content: str,
        word_count: int,
        words_per_chapter: int,
        beats: list[str],
        dormant_threads: list[str],
        forbidden_reveals: list[str],
        hard_constraints: str,
        chapter_mandate: str,
    ) -> GoalVerdict:
        deterministic = []
        wc_gap = word_count_gap(word_count, words_per_chapter)
        if wc_gap:
            deterministic.append(wc_gap)

        llm_verdict = await self._llm_verdict(
            chapter_id=chapter_id,
            content=content,
            word_count=word_count,
            words_per_chapter=words_per_chapter,
            beats=beats,
            dormant_threads=dormant_threads,
            forbidden_reveals=forbidden_reveals,
            hard_constraints=hard_constraints,
            chapter_mandate=chapter_mandate,
        )
        if deterministic:
            llm_verdict.satisfied = False
            llm_verdict.gaps = [*deterministic, *llm_verdict.gaps]
            if not llm_verdict.summary:
                llm_verdict.summary = deterministic[0].detail
        return llm_verdict

    async def _llm_verdict(self, **kwargs) -> GoalVerdict:
        prompt = GOAL_TEMPLATE.format(
            chapter_id=kwargs["chapter_id"],
            word_count=kwargs["word_count"],
            words_per_chapter=kwargs["words_per_chapter"],
            beats=_as_prompt_list(kwargs["beats"]),
            dormant_threads=_as_prompt_list(kwargs["dormant_threads"]),
            forbidden_reveals=_as_prompt_list(kwargs["forbidden_reveals"]),
            hard_constraints=kwargs["hard_constraints"] or "（无）",
            chapter_mandate=kwargs["chapter_mandate"] or "（无）",
            content=kwargs["content"],
        )
        try:
            raw = await self._llm.generate(
                LLMRequest(
                    task=LLMTask.GOAL_VERIFY,
                    system=GOAL_SYSTEM,
                    prompt=prompt,
                    json_mode=True,
                )
            )
            data = parse_llm_json(raw)
        except (json.JSONDecodeError, TypeError, ValueError):
            return GoalVerdict(satisfied=True, summary="验收器输出无法解析，仅通过长度检查")

        gaps: list[GoalGap] = []
        for item in data.get("gaps") or []:
            if isinstance(item, str):
                gaps.append(GoalGap(code="other", detail=item))
                continue
            if not isinstance(item, dict):
                continue
            detail = str(item.get("detail") or "").strip()
            if not detail:
                continue
            gaps.append(GoalGap(code=str(item.get("code") or "other"), detail=detail))

        satisfied = bool(data.get("satisfied")) and not gaps
        return GoalVerdict(
            satisfied=satisfied,
            impossible=bool(data.get("impossible")),
            gaps=gaps,
            summary=str(data.get("summary") or ""),
        )


def _as_prompt_list(values: list[str]) -> str:
    items = [str(item).strip() for item in values if str(item).strip()]
    if not items:
        return "（无）"
    return json.dumps(items, ensure_ascii=False)
