import json
from typing import Any

from xsagent.agents.prompts.defaults import DEFAULT_WRITE_INSTRUCTION
from xsagent.domain.narrative.hard_constraints import (
    hard_constraints_from_mandate,
    hard_constraints_prompt_text,
)
from xsagent.domain.narrative.mandate import ChapterMandateBuilder
from xsagent.domain.common.scope import (
    find_volume_for_chapter,
    scoped_context_for_chapter,
    volume_scope_text,
)
from xsagent.domain.common.style_rules import style_rules_prompt_text
from xsagent.domain.common.spoiler import (
    bible_summary_text,
    chapter_number,
    spoiler_safe_bible_sections,
)
from xsagent.domain.common.text import bible_sections
from xsagent.domain.memory.service import BibleService
from xsagent.domain.outline.service import OutlineService
from xsagent.domain.project.models import Project
from xsagent.domain.writing.checkpoint import (
    CheckpointStore,
    render_checkpoint,
    render_session_checkpoints,
    take_ending_slice,
)
from xsagent.domain.writing.service import ChapterService
from xsagent.storage.project_store import ProjectStore

# L3 滚动窗口：写作第 N 章时注入第 N-1、N-2、N-3 章的状态，而非全文
ROLLING_WINDOW_SIZE = 3


def trim_chapter_for_context(content_md: str, max_chars: int) -> str:
    text = content_md.strip()
    if len(text) <= max_chars:
        return text

    head_budget = min(500, max_chars // 4)
    tail_budget = max_chars - head_budget - 20
    if tail_budget < 200:
        return text[:max_chars] + "\n…（已截断）"

    return f"{text[:head_budget]}\n\n…（中段省略）…\n\n{text[-tail_budget:]}"


class WritingContextBuilder:
    def __init__(
        self,
        store: ProjectStore,
        bible: BibleService,
        chapters: ChapterService,
        outlines: OutlineService,
    ) -> None:
        self._store = store
        self._bible = bible
        self._chapters = chapters
        self._outlines = outlines
        self._mandate_builder = ChapterMandateBuilder()
        self._checkpoints = CheckpointStore(bible)

    def build(self, project: Project, chapter_id: str, instruction: str) -> dict[str, Any]:
        target_no = chapter_number(chapter_id)
        master = self._outlines.get_master(project.id)
        volumes = [volume.model_dump() for volume in self._outlines.list_volumes(project.id)]
        volume = find_volume_for_chapter(volumes, target_no)
        blueprint = self._safe_blueprint(project.id, chapter_id)
        bible_sections_data = {
            section: self._bible.get_section(project.id, section)
            for section in bible_sections()
        }
        mandate = self._mandate_builder.build(
            chapter_id=chapter_id,
            chapter_no=target_no,
            volume=volume,
            plot_section=bible_sections_data.get("plot", {}),
            characters_section=bible_sections_data.get("characters", {}),
        )
        hard = blueprint.get("hard_constraints") or {}
        if not hard:
            hard = hard_constraints_from_mandate(mandate)
        author_notes = str(blueprint.get("author_notes") or "").strip()
        soft_constraints = blueprint.get("constraints") or []
        soft_text = "；".join(str(c) for c in soft_constraints) if soft_constraints else "（无）"
        dormant_threads = (
            blueprint.get("dormant_threads") or hard.get("dormant_threads") or []
        )
        beats = blueprint.get("beats") or []
        blueprint_lite = {
            "chapter_id": blueprint.get("chapter_id", chapter_id),
            "title": blueprint.get("title", chapter_id),
            "beats": beats,
            "chapter_role": blueprint.get("chapter_role") or hard.get("chapter_role"),
            "primary_thread": blueprint.get("primary_thread") or hard.get("primary_thread"),
            "dormant_threads": dormant_threads,
            "status": blueprint.get("status", "pending"),
        }
        scoped_context = scoped_context_for_chapter(
            bible_sections=bible_sections_data,
            volume=volume,
            chapter_no=target_no,
            master_acts=list(master.get("acts", [])),
        )
        volume_scope = volume_scope_text(volume, target_no) if volume else "{}"
        bible_summary = self._bible_summary(project.id, target_no, master_acts=master.get("acts", []))
        notes = self._bible.get_section(project.id, "notes")
        style_notes = notes.get("style_notes", "") or "（无）"
        style_rules = style_rules_prompt_text(notes.get("style_rules") or [])
        stored_summaries: dict[str, str] = notes.get("chapter_summaries", {})
        recent_window = self._rolling_window_text(
            project.id, chapter_id, stored_summaries
        )
        config = self._store.read_yaml(self._store.project_path(project.id) / "config.yaml")
        forbidden_reveals = list(volume.get("forbidden_reveals") or []) if volume else []

        return {
            "project": project,
            "chapter_id": chapter_id,
            "instruction": instruction or DEFAULT_WRITE_INSTRUCTION,
            "genre": project.genre,
            "name": project.name,
            "intervention_level": project.intervention_level.value,
            "volume_scope": volume_scope[:1200],
            "scoped_context": scoped_context[:1500],
            "chapter_mandate": mandate.to_prompt_text()[:1200],
            "hard_constraints": hard_constraints_prompt_text(hard)[:1000],
            "author_notes": author_notes[:600] or "（无）",
            "soft_constraints": soft_text[:400],
            "chapter_blueprint": json.dumps(blueprint_lite, ensure_ascii=False)[:800],
            "bible_summary": bible_summary[:1200],
            "style_rules": style_rules,
            "style_notes": style_notes,
            "words_per_chapter": config.get("words_per_chapter", 3000),
            "recent_chapters_window": recent_window,
            "session_checkpoint": self._session_checkpoint_text(project.id, chapter_id),
            "goal_feedback": "（无）",
            "beats": beats,
            "dormant_threads": dormant_threads,
            "forbidden_reveals": forbidden_reveals,
            "chapter_role": str(blueprint_lite.get("chapter_role") or ""),
        }

    def _rolling_window_text(
        self,
        project_id: str,
        chapter_id: str,
        stored_summaries: dict[str, str],
    ) -> str:
        target_no = chapter_number(chapter_id)
        if target_no <= 1:
            return "（尚无已写章节，本章为开篇。）"

        summaries = self._chapters.list_chapters(project_id)
        prior = [s for s in summaries if chapter_number(s.id) < target_no]
        prior.sort(key=lambda s: chapter_number(s.id))
        window = prior[-ROLLING_WINDOW_SIZE:]
        if not window:
            return "（尚无已写章节，本章为开篇。）"

        checkpoints = self._checkpoints.get_all(project_id)
        blocks: list[str] = []
        immediate_id = window[-1].id
        for item in window:
            is_immediate_prior = item.id == immediate_id
            checkpoint = checkpoints.get(item.id)

            if is_immediate_prior:
                if checkpoint and checkpoint.ending_slice:
                    body = checkpoint.ending_slice
                else:
                    chapter = self._chapters.get_chapter(project_id, item.id)
                    body = take_ending_slice(chapter.content_md)
                label = "章末切片"
            elif checkpoint:
                body = render_checkpoint(checkpoint)
                label = "状态记录"
            elif item.id in stored_summaries:
                body = stored_summaries[item.id]
                label = "压缩摘要"
            else:
                chapter = self._chapters.get_chapter(project_id, item.id)
                body = trim_chapter_for_context(chapter.content_md, 4000)
                label = "正文"

            blocks.append(f"### {item.id} {item.title}（{label}）\n{body}")

        return "\n\n---\n\n".join(blocks)

    def _session_checkpoint_text(self, project_id: str, chapter_id: str) -> str:
        target_no = chapter_number(chapter_id)
        checkpoints = [
            item
            for item in self._checkpoints.get_all(project_id).values()
            if chapter_number(item.chapter_id) < target_no
        ]
        checkpoints.sort(key=lambda item: chapter_number(item.chapter_id))
        return render_session_checkpoints(checkpoints[-ROLLING_WINDOW_SIZE:])

    def _bible_summary(
        self,
        project_id: str,
        chapter_no: int,
        *,
        master_acts: list[dict[str, Any]] | None = None,
    ) -> str:
        sections = {
            section: self._bible.get_section(project_id, section)
            for section in bible_sections()
        }
        filtered = spoiler_safe_bible_sections(
            sections,
            chapter_no,
            master_acts=master_acts,
        )
        return bible_summary_text(filtered)

    def _safe_blueprint(self, project_id: str, chapter_id: str) -> dict[str, Any]:
        try:
            bp = self._outlines.get_chapter_blueprint(project_id, chapter_id)
            return bp.model_dump()
        except Exception:
            return {"chapter_id": chapter_id, "title": chapter_id, "beats": [], "status": "pending"}
