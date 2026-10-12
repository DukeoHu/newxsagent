import json
import re

from xsagent.agents.prompts import (
    ONBOARDING_GENERATE_SYSTEM,
    ONBOARDING_GENERATE_TEMPLATE,
    ONBOARDING_QUESTION_SYSTEM,
    ONBOARDING_QUESTION_TEMPLATE,
)
from xsagent.domain.onboarding.models import OnboardingSession
from xsagent.llm.base import LLMProvider, LLMRequest, LLMTask


class OnboardingAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def next_question(self, session: OnboardingSession) -> dict:
        user_answers = [t.content for t in session.turns if t.role == "user"]
        answered = len(user_answers)
        transcript = self._format_transcript(session.turns)
        prompt = ONBOARDING_QUESTION_TEMPLATE.format(
            project_name=session.context.get("name", ""),
            genre=session.context.get("genre", ""),
            turn_index=answered + 1,
            min_turns=3,
            max_turns=6,
            transcript=transcript or "（尚无对话）",
        )
        raw = await self._llm.generate(
            LLMRequest(
                task=LLMTask.ONBOARDING_QUESTION,
                system=ONBOARDING_QUESTION_SYSTEM,
                prompt=prompt,
                json_mode=True,
            )
        )
        return self._parse_json(raw)

    async def generate_bible_draft(self, session: OnboardingSession) -> dict:
        transcript = self._format_transcript(session.turns)
        prompt = ONBOARDING_GENERATE_TEMPLATE.format(
            project_name=session.context.get("name", ""),
            genre=session.context.get("genre", ""),
            transcript=transcript,
        )
        raw = await self._llm.generate(
            LLMRequest(
                task=LLMTask.ONBOARDING_GENERATE,
                system=ONBOARDING_GENERATE_SYSTEM,
                prompt=prompt,
                json_mode=True,
            )
        )
        data = self._parse_json(raw)
        bible = data.get("bible", data)
        return self._normalize_bible(bible)

    def _format_transcript(self, turns: list) -> str:
        lines: list[str] = []
        for turn in turns:
            label = "引导师" if turn.role == "assistant" else "作者"
            lines.append(f"{label}：{turn.content}")
        return "\n".join(lines)

    def _normalize_bible(self, bible: dict) -> dict:
        sections = ("characters", "plot", "timeline", "world", "notes")
        normalized: dict = {}
        for section in sections:
            data = bible.get(section, {})
            if not isinstance(data, dict):
                data = {}
            data.setdefault("locked_fields", [])
            if section == "characters":
                data.setdefault("characters", [])
            elif section == "plot":
                data.setdefault("acts", [])
                data.setdefault("themes", [])
                data.setdefault("foreshadowing", [])
            elif section == "timeline":
                data.setdefault("events", [])
            elif section == "world":
                data.setdefault("rules", [])
                data.setdefault("locations", [])
            elif section == "notes":
                data.setdefault("style_notes", "")
                data.setdefault("author_notes", "")
                data.setdefault("spoiler_vault", "")
                data["style_rules"] = self._normalize_style_rules(data.get("style_rules"))
            normalized[section] = data
        return normalized

    def _normalize_style_rules(self, raw: object) -> list[dict]:
        allowed_categories = {
            "perspective",
            "tone",
            "pacing",
            "dialogue",
            "diction",
            "technique",
            "taboo",
        }
        allowed_priorities = {"must", "should", "prefer"}
        if not isinstance(raw, list):
            return []
        rules: list[dict] = []
        for index, item in enumerate(raw, start=1):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip()
            description = str(item.get("description", "")).strip()
            if not title and not description:
                continue
            category = str(item.get("category", "tone")).strip().lower()
            if category not in allowed_categories:
                category = "tone"
            priority = str(item.get("priority", "should")).strip().lower()
            if priority not in allowed_priorities:
                priority = "should"
            rule_id = str(item.get("id", "")).strip() or f"sr_{index}"
            rules.append(
                {
                    "id": rule_id,
                    "category": category,
                    "title": title or f"风格规则 {index}",
                    "description": description or title,
                    "priority": priority,
                }
            )
        return rules

    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()
        fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if fence:
            text = fence.group(1)
        return json.loads(text)
