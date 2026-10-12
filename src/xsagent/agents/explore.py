from __future__ import annotations

import json
from uuid import uuid4

from pydantic import ValidationError

from xsagent.agents.prompts.explore import (
    EXPLORE_SYSTEM,
    EXPLORE_TEMPLATE,
    JUDGE_SYSTEM,
    JUDGE_TEMPLATE,
    fallback_options,
)
from xsagent.domain.explore.models import ExploreOption
from xsagent.llm.base import LLMProvider, LLMRequest, LLMTask
from xsagent.llm.parse import parse_llm_json

MAX_MODE_CANDIDATES = 3


class ExploreAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def propose(
        self,
        *,
        chapter_id: str,
        prompt: str,
        count: int,
        context: dict | None = None,
    ) -> list[ExploreOption]:
        ctx = context or {}
        try:
            raw = await self._llm.generate(
                LLMRequest(
                    task=LLMTask.EXPLORE,
                    system=EXPLORE_SYSTEM,
                    prompt=EXPLORE_TEMPLATE.format(
                        chapter_id=chapter_id,
                        count=count,
                        prompt=prompt,
                        hard_constraints=ctx.get("hard_constraints") or "（无）",
                        chapter_mandate=ctx.get("chapter_mandate") or "（无）",
                        bible_summary=ctx.get("bible_summary") or "（无）",
                    ),
                    json_mode=True,
                )
            )
            options = self._parse_options(raw, chapter_id=chapter_id, count=count)
        except (ValueError, TypeError, ValidationError, KeyError):
            options = []
        if len(options) < count:
            options.extend(fallback_options(chapter_id, prompt, count))
        return options[:count]

    async def judge(
        self,
        options: list[ExploreOption],
        *,
        context: dict | None = None,
    ) -> tuple[str, str]:
        if not options:
            return "", ""
        if len(options) == 1:
            return options[0].option_id, "唯一候选"
        ctx = context or {}
        payload = json.dumps(
            [item.model_dump() for item in options],
            ensure_ascii=False,
        )
        try:
            raw = await self._llm.generate(
                LLMRequest(
                    task=LLMTask.JUDGE,
                    system=JUDGE_SYSTEM,
                    prompt=JUDGE_TEMPLATE.format(
                        chapter_mandate=ctx.get("chapter_mandate") or "（无）",
                        hard_constraints=ctx.get("hard_constraints") or "（无）",
                        candidates=payload,
                    ),
                    json_mode=True,
                )
            )
            data = parse_llm_json(raw)
            winner = str(data.get("winner_option_id") or "")
            reason = str(data.get("reason") or "")
            if any(item.option_id == winner for item in options):
                return winner, reason or "评审选中"
        except (ValueError, TypeError, KeyError):
            pass
        safest = min(options, key=lambda item: {"low": 0, "medium": 1, "high": 2}.get(item.risk_level, 9))
        return safest.option_id, "评审无法解析，回退到风险最低方案"

    async def select_plan(
        self,
        *,
        chapter_id: str,
        prompt: str,
        context: dict | None = None,
        count: int = MAX_MODE_CANDIDATES,
    ) -> ExploreOption:
        options = await self.propose(
            chapter_id=chapter_id,
            prompt=prompt,
            count=count,
            context=context,
        )
        winner_id, _reason = await self.judge(options, context=context)
        for item in options:
            if item.option_id == winner_id:
                return item
        return options[0]

    def _parse_options(self, raw: str, *, chapter_id: str, count: int) -> list[ExploreOption]:
        data = parse_llm_json(raw)
        rows = data.get("options") or []
        options: list[ExploreOption] = []
        for index, row in enumerate(rows[:count], start=1):
            if not isinstance(row, dict):
                continue
            risk = str(row.get("risk_level") or "medium")
            if risk not in {"low", "medium", "high"}:
                risk = "medium"
            beats = [str(b) for b in (row.get("beats") or []) if str(b).strip()]
            constraints = [str(c) for c in (row.get("constraints") or []) if str(c).strip()]
            options.append(
                ExploreOption(
                    option_id=str(row.get("option_id") or f"opt_{uuid4().hex[:8]}"),
                    chapter_id=chapter_id,
                    title=str(row.get("title") or f"方案 {index}").strip(),
                    summary=str(row.get("summary") or "").strip() or f"方案 {index}",
                    beats=beats or [f"{chapter_id} 推进主冲突"],
                    constraints=constraints or ["不破坏已锁定设定"],
                    risk_level=risk,  # type: ignore[arg-type]
                )
            )
        return options
