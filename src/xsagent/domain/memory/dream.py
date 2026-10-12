from __future__ import annotations

from pydantic import BaseModel, Field

from xsagent.domain.memory.service import BibleService
from xsagent.domain.writing.service import ChapterService


class DreamReport(BaseModel):
    orphan_summaries_removed: list[str] = Field(default_factory=list)
    orphan_checkpoints_removed: list[str] = Field(default_factory=list)
    duplicate_rules_removed: int = 0
    notes_updated: bool = False


def run_heuristic_dream(
    bible: BibleService,
    chapters: ChapterService,
    project_id: str,
) -> DreamReport:
    """清理失效引用与重复规则。不调用模型，可在主循环里同步执行。"""
    notes = bible.get_section(project_id, "notes")
    living = {item.id for item in chapters.list_chapters(project_id)}
    summaries = dict(notes.get("chapter_summaries") or {})
    checkpoints = dict(notes.get("chapter_checkpoints") or {})

    orphan_summaries = [cid for cid in list(summaries) if cid not in living]
    orphan_checkpoints = [cid for cid in list(checkpoints) if cid not in living]
    for cid in orphan_summaries:
        summaries.pop(cid, None)
    for cid in orphan_checkpoints:
        checkpoints.pop(cid, None)

    rules = [rule for rule in (notes.get("style_rules") or []) if isinstance(rule, dict)]
    seen: set[str] = set()
    unique: list[dict] = []
    duplicates = 0
    for rule in rules:
        title = str(rule.get("title") or "").strip()
        key = title or str(rule.get("id") or "")
        if key and key in seen:
            duplicates += 1
            continue
        if key:
            seen.add(key)
        unique.append(rule)

    notes["chapter_summaries"] = summaries
    notes["chapter_checkpoints"] = checkpoints
    notes["style_rules"] = unique
    changed = bool(orphan_summaries or orphan_checkpoints or duplicates)
    if changed:
        bible.put_section(project_id, "notes", notes)
    return DreamReport(
        orphan_summaries_removed=orphan_summaries,
        orphan_checkpoints_removed=orphan_checkpoints,
        duplicate_rules_removed=duplicates,
        notes_updated=changed,
    )
