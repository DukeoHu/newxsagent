import json
import re

from xsagent.agents.prompts import (
    OUTLINE_CHAPTERS_SYSTEM,
    OUTLINE_CHAPTERS_TEMPLATE,
    OUTLINE_MASTER_SYSTEM,
    OUTLINE_MASTER_TEMPLATE,
    OUTLINE_THREADS_SYSTEM,
    OUTLINE_THREADS_TEMPLATE,
)
from xsagent.llm.base import LLMProvider, LLMRequest, LLMTask


class OutlinePlannerAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def generate_master(
        self,
        *,
        project_name: str,
        genre: str,
        bible_summary: str,
        current_master: dict,
        total_chapters: int,
        volume_count: int,
    ) -> dict:
        prompt = OUTLINE_MASTER_TEMPLATE.format(
            project_name=project_name,
            genre=genre,
            bible_summary=bible_summary[:4000],
            current_master=json.dumps(current_master, ensure_ascii=False)[:1500],
            total_chapters=total_chapters,
            volume_count=volume_count,
        )
        raw = await self._llm.generate(
            LLMRequest(
                task=LLMTask.OUTLINE_MASTER,
                system=OUTLINE_MASTER_SYSTEM,
                prompt=prompt,
                json_mode=True,
            )
        )
        return self._parse_json(raw)

    async def generate_threads(
        self,
        *,
        project_name: str,
        genre: str,
        bible_summary: str,
        volumes: list[dict],
    ) -> dict:
        prompt = OUTLINE_THREADS_TEMPLATE.format(
            project_name=project_name,
            genre=genre,
            bible_summary=bible_summary[:4000],
            volumes_json=json.dumps(volumes, ensure_ascii=False)[:5000],
        )
        raw = await self._llm.generate(
            LLMRequest(
                task=LLMTask.OUTLINE_THREADS,
                system=OUTLINE_THREADS_SYSTEM,
                prompt=prompt,
                json_mode=True,
            )
        )
        return self._parse_json(raw)

    async def generate_chapter_batch(
        self,
        *,
        project_name: str,
        genre: str,
        chapter_mandates: str,
        volume_scope: str,
        scoped_context: str,
        chapter_ids: list[str],
        neighbor_context: str,
        spoiler_guard: str,
    ) -> dict:
        prompt = OUTLINE_CHAPTERS_TEMPLATE.format(
            project_name=project_name,
            genre=genre,
            chapter_mandates=chapter_mandates[:6000],
            volume_scope=volume_scope[:2000],
            scoped_context=scoped_context[:3500],
            chapter_ids=", ".join(chapter_ids),
            neighbor_context=neighbor_context[:2000] or "（无）",
            spoiler_guard=spoiler_guard,
        )
        raw = await self._llm.generate(
            LLMRequest(
                task=LLMTask.OUTLINE_CHAPTERS,
                system=OUTLINE_CHAPTERS_SYSTEM,
                prompt=prompt,
                json_mode=True,
            )
        )
        return self._parse_json(raw)

    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()
        fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if fence:
            text = fence.group(1)
        return json.loads(text)
