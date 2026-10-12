from __future__ import annotations

import json
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError

from xsagent.agents.prompts.maintenance import (
    DISTILL_SYSTEM,
    DISTILL_TEMPLATE,
    DREAM_SYSTEM,
    DREAM_TEMPLATE,
)
from xsagent.domain.memory.dream import DreamReport, run_heuristic_dream
from xsagent.domain.memory.service import BibleService
from xsagent.domain.writing.checkpoint import CheckpointStore, render_session_checkpoints
from xsagent.domain.writing.service import ChapterService
from xsagent.llm.base import LLMProvider, LLMRequest, LLMTask
from xsagent.llm.parse import parse_llm_json


class DreamAgent:
    def __init__(self, llm: LLMProvider, bible: BibleService, chapters: ChapterService) -> None:
        self._llm = llm
        self._bible = bible
        self._chapters = chapters
        self._checkpoints = CheckpointStore(bible)

    async def run(self, project_id: str) -> DreamReport:
        report = run_heuristic_dream(self._bible, self._chapters, project_id)
        notes = self._bible.get_section(project_id, "notes")
        characters = self._bible.get_section(project_id, "characters")
        checkpoints = list(self._checkpoints.get_all(project_id).values())
        try:
            raw = await self._llm.generate(
                LLMRequest(
                    task=LLMTask.DREAM,
                    system=DREAM_SYSTEM,
                    prompt=DREAM_TEMPLATE.format(
                        notes=json.dumps(
                            {
                                "style_notes": notes.get("style_notes", ""),
                                "author_notes": notes.get("author_notes", ""),
                            },
                            ensure_ascii=False,
                        )[:4000],
                        characters=json.dumps(characters, ensure_ascii=False)[:4000],
                        checkpoints=render_session_checkpoints(checkpoints[-5:])[:4000],
                    ),
                    json_mode=True,
                )
            )
            data = parse_llm_json(raw)
        except (ValueError, TypeError, ValidationError):
            return report

        compressed = str(data.get("compress_style_notes") or "").strip()
        drop_keys = [str(k) for k in (data.get("drop_note_keys") or []) if str(k).strip()]
        changed = False
        if compressed and compressed != notes.get("style_notes"):
            notes["style_notes"] = compressed[:1200]
            changed = True
        for key in drop_keys:
            if key == "author_notes" and notes.get(key):
                notes[key] = ""
                changed = True
        if changed:
            self._bible.put_section(project_id, "notes", notes)
            report.notes_updated = True
        return report


class DistillReport(BaseModel):
    added_rules: list[dict] = Field(default_factory=list)
    skipped_existing: int = 0
    source_decisions: int = 0


class DistillAgent:
    def __init__(self, llm: LLMProvider, bible: BibleService) -> None:
        self._llm = llm
        self._bible = bible

    async def run(self, project_id: str, decisions: list[str]) -> DistillReport:
        notes = self._bible.get_section(project_id, "notes")
        existing = [rule for rule in (notes.get("style_rules") or []) if isinstance(rule, dict)]
        existing_titles = {
            str(rule.get("title") or "").strip() for rule in existing if rule.get("title")
        }
        if not decisions:
            return DistillReport(source_decisions=0)

        try:
            raw = await self._llm.generate(
                LLMRequest(
                    task=LLMTask.DISTILL,
                    system=DISTILL_SYSTEM,
                    prompt=DISTILL_TEMPLATE.format(
                        existing_rules=json.dumps(existing, ensure_ascii=False)[:3000],
                        decisions="\n".join(f"- {item}" for item in decisions[:40]),
                    ),
                    json_mode=True,
                )
            )
            data = parse_llm_json(raw)
        except (ValueError, TypeError, KeyError):
            return DistillReport(source_decisions=len(decisions))

        added: list[dict] = []
        skipped = 0
        for row in data.get("rules") or []:
            if not isinstance(row, dict):
                continue
            title = str(row.get("title") or "").strip()
            description = str(row.get("description") or "").strip()
            if not title or not description:
                continue
            if title in existing_titles:
                skipped += 1
                continue
            category = str(row.get("category") or "tone")
            priority = str(row.get("priority") or "should")
            if category not in {
                "perspective",
                "tone",
                "pacing",
                "dialogue",
                "diction",
                "technique",
                "taboo",
            }:
                category = "tone"
            if priority not in {"must", "should", "prefer"}:
                priority = "should"
            rule = {
                "id": f"sr_distill_{uuid4().hex[:8]}",
                "category": category,
                "title": title,
                "description": description,
                "priority": priority,
            }
            existing.append(rule)
            existing_titles.add(title)
            added.append(rule)

        if added:
            notes["style_rules"] = existing
            self._bible.put_section(project_id, "notes", notes)
        return DistillReport(
            added_rules=added,
            skipped_existing=skipped,
            source_decisions=len(decisions),
        )
