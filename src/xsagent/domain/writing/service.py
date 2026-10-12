import re

from xsagent.core.exceptions import (
    ChapterAlreadyExistsError,
    ChapterNotFoundError,
    ProjectNotFoundError,
)
from xsagent.domain.common.text import (
    chapter_id_from_filename,
    count_words,
    parse_chapter_title,
)
from xsagent.domain.writing.models import Chapter, ChapterCreate, ChapterSummary, ChapterUpdate
from xsagent.storage.project_store import ProjectStore


class ChapterService:
    def __init__(self, store: ProjectStore) -> None:
        self._store = store

    def list_chapters(self, project_id: str) -> list[ChapterSummary]:
        self._ensure_project(project_id)
        summaries: list[ChapterSummary] = []
        for filename in self._store.list_chapters(project_id):
            chapter = self.get_chapter(project_id, chapter_id_from_filename(filename))
            summaries.append(
                ChapterSummary(
                    id=chapter.id,
                    title=chapter.title,
                    word_count=chapter.word_count,
                    filename=chapter.filename,
                )
            )
        return summaries

    def get_chapter(self, project_id: str, chapter_id: str) -> Chapter:
        self._ensure_project(project_id)
        path = self._chapter_path(project_id, chapter_id)
        if not path.exists():
            raise ChapterNotFoundError(project_id, chapter_id)
        content_md = self._store.read_md(path)
        filename = f"{chapter_id}.md"
        title = parse_chapter_title(content_md, chapter_id)
        return Chapter(
            id=chapter_id,
            title=title,
            content_md=content_md,
            word_count=count_words(content_md),
            filename=filename,
        )

    def create_chapter(self, project_id: str, payload: ChapterCreate) -> Chapter:
        self._ensure_project(project_id)
        path = self._chapter_path(project_id, payload.id)
        if path.exists():
            raise ChapterAlreadyExistsError(payload.id)

        title = payload.title or payload.id
        if payload.content_md.strip():
            content = payload.content_md
        else:
            content = f"# {title}\n\n"
        self._store.write_md(path, content)
        return self.get_chapter(project_id, payload.id)

    def update_chapter(
        self, project_id: str, chapter_id: str, payload: ChapterUpdate
    ) -> Chapter:
        chapter = self.get_chapter(project_id, chapter_id)
        content = payload.content_md if payload.content_md is not None else chapter.content_md
        if payload.title is not None:
            lines = content.splitlines()
            if lines and lines[0].strip().startswith("# "):
                lines[0] = f"# {payload.title}"
                content = "\n".join(lines)
                if not content.endswith("\n"):
                    content += "\n"
            else:
                content = f"# {payload.title}\n\n{content.lstrip()}"
        self._store.write_md(self._chapter_path(project_id, chapter_id), content)
        return self.get_chapter(project_id, chapter_id)

    def delete_chapter(self, project_id: str, chapter_id: str) -> None:
        self._ensure_project(project_id)
        path = self._chapter_path(project_id, chapter_id)
        if not path.exists():
            raise ChapterNotFoundError(project_id, chapter_id)
        path.unlink()
        self._cleanup_after_delete(project_id, chapter_id)

    def save_generated(self, project_id: str, chapter_id: str, content_md: str) -> Chapter:
        self._ensure_project(project_id)
        path = self._chapter_path(project_id, chapter_id)
        if path.exists():
            return self.update_chapter(project_id, chapter_id, ChapterUpdate(content_md=content_md))
        title = parse_chapter_title(content_md, chapter_id)
        return self.create_chapter(
            project_id, ChapterCreate(id=chapter_id, title=title, content_md=content_md)
        )

    def resolve_chapter_id(self, project_id: str, requested: str | None = None) -> str:
        if requested:
            return requested
        summaries = self.list_chapters(project_id)
        if not summaries:
            return "ch_001"
        latest = summaries[-1]
        if latest.word_count < 30:
            return latest.id
        match = re.match(r"ch_(\d+)", latest.id)
        num = int(match.group(1)) + 1 if match else len(summaries) + 1
        return f"ch_{num:03d}"

    def _chapter_path(self, project_id: str, chapter_id: str):
        return self._store.project_path(project_id) / "chapters" / f"{chapter_id}.md"

    def _cleanup_after_delete(self, project_id: str, chapter_id: str) -> None:
        notes_path = self._store.project_path(project_id) / "story_bible" / "notes.json"
        if notes_path.exists():
            notes = self._store.read_json(notes_path)
            summaries = notes.get("chapter_summaries", {})
            checkpoints = notes.get("chapter_checkpoints", {})
            changed = False
            if chapter_id in summaries:
                del summaries[chapter_id]
                notes["chapter_summaries"] = summaries
                changed = True
            if chapter_id in checkpoints:
                del checkpoints[chapter_id]
                notes["chapter_checkpoints"] = checkpoints
                changed = True
            if changed:
                self._store.write_json(notes_path, notes)

        blueprint_path = (
            self._store.project_path(project_id) / "outlines" / "chapters" / f"{chapter_id}.json"
        )
        if blueprint_path.exists():
            blueprint = self._store.read_json(blueprint_path)
            blueprint["status"] = "pending"
            self._store.write_json(blueprint_path, blueprint)

    def _ensure_project(self, project_id: str) -> None:
        if not self._store.exists(project_id):
            raise ProjectNotFoundError(project_id)
