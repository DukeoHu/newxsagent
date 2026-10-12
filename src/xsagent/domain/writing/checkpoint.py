from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from xsagent.domain.memory.service import BibleService

ENDING_SLICE_MAX_CHARS = 2000
OLDER_CHECKPOINT_MAX_CHARS = 1200
SESSION_CHECKPOINT_MAX_CHARS = 2400
HEURISTIC_SUMMARY_MAX_CHARS = 400


class ChapterCheckpoint(BaseModel):
    chapter_id: str
    intent: str = ""
    next_action: str = ""
    constraints: list[str] = Field(default_factory=list)
    open_loops: list[str] = Field(default_factory=list)
    current_work: str = ""
    involved_characters: list[str] = Field(default_factory=list)
    discoveries: list[str] = Field(default_factory=list)
    errors_and_fixes: list[str] = Field(default_factory=list)
    character_states: dict[str, str] = Field(default_factory=dict)
    design_decisions: list[str] = Field(default_factory=list)
    notes: str = ""
    ending_slice: str = ""
    summary: str = ""


def take_ending_slice(content_md: str, max_chars: int = ENDING_SLICE_MAX_CHARS) -> str:
    text = content_md.strip()
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def heuristic_summary(content_md: str, max_chars: int = HEURISTIC_SUMMARY_MAX_CHARS) -> str:
    lines = [
        ln.strip()
        for ln in content_md.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    text = " ".join(lines)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"


def heuristic_checkpoint(
    chapter_id: str,
    content_md: str,
    *,
    title: str = "",
) -> ChapterCheckpoint:
    return ChapterCheckpoint(
        chapter_id=chapter_id,
        intent=title or chapter_id,
        current_work=title or chapter_id,
        ending_slice=take_ending_slice(content_md),
        summary=heuristic_summary(content_md),
    )


def _join_list(values: list[str]) -> str:
    return "；".join(item for item in values if item) or "（无）"


def render_checkpoint(
    checkpoint: ChapterCheckpoint,
    *,
    max_chars: int = OLDER_CHECKPOINT_MAX_CHARS,
) -> str:
    states = "；".join(
        f"{name}：{state}" for name, state in checkpoint.character_states.items()
    ) or "（无）"
    text = "\n".join(
        [
            f"意图：{checkpoint.intent or '（无）'}",
            f"已完成：{checkpoint.current_work or '（无）'}",
            f"下一步：{checkpoint.next_action or '（无）'}",
            f"开放钩子：{_join_list(checkpoint.open_loops)}",
            f"人物状态：{states}",
            f"约束：{_join_list(checkpoint.constraints)}",
            f"发现：{_join_list(checkpoint.discoveries)}",
            f"摘要：{checkpoint.summary or '（无）'}",
        ]
    )
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def render_session_checkpoints(
    checkpoints: list[ChapterCheckpoint],
    *,
    max_chars: int = SESSION_CHECKPOINT_MAX_CHARS,
) -> str:
    if not checkpoints:
        return "（尚无会话状态记录）"
    blocks = [
        f"### {item.chapter_id}\n{render_checkpoint(item, max_chars=800)}"
        for item in checkpoints
    ]
    text = "\n\n".join(blocks)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


class CheckpointStore:
    def __init__(self, bible: BibleService) -> None:
        self._bible = bible

    def get_all(self, project_id: str) -> dict[str, ChapterCheckpoint]:
        notes = self._bible.get_section(project_id, "notes")
        raw: dict[str, Any] = notes.get("chapter_checkpoints") or {}
        result: dict[str, ChapterCheckpoint] = {}
        for chapter_id, payload in raw.items():
            if not isinstance(payload, dict):
                continue
            result[chapter_id] = ChapterCheckpoint.model_validate(
                {**payload, "chapter_id": chapter_id}
            )
        return result

    def get(self, project_id: str, chapter_id: str) -> ChapterCheckpoint | None:
        return self.get_all(project_id).get(chapter_id)

    def put(self, project_id: str, checkpoint: ChapterCheckpoint) -> ChapterCheckpoint:
        notes = self._bible.get_section(project_id, "notes")
        checkpoints = dict(notes.get("chapter_checkpoints") or {})
        checkpoints[checkpoint.chapter_id] = checkpoint.model_dump()
        notes["chapter_checkpoints"] = checkpoints
        summaries = dict(notes.get("chapter_summaries") or {})
        if checkpoint.summary:
            summaries[checkpoint.chapter_id] = checkpoint.summary
        notes["chapter_summaries"] = summaries
        self._bible.put_section(project_id, "notes", notes)
        return checkpoint

    def delete(self, project_id: str, chapter_id: str) -> None:
        notes = self._bible.get_section(project_id, "notes")
        checkpoints = dict(notes.get("chapter_checkpoints") or {})
        summaries = dict(notes.get("chapter_summaries") or {})
        checkpoints.pop(chapter_id, None)
        summaries.pop(chapter_id, None)
        notes["chapter_checkpoints"] = checkpoints
        notes["chapter_summaries"] = summaries
        self._bible.put_section(project_id, "notes", notes)
