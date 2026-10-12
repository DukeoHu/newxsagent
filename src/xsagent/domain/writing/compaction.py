from xsagent.domain.memory.dream import run_heuristic_dream
from xsagent.domain.memory.service import BibleService
from xsagent.domain.writing.checkpoint import CheckpointStore, heuristic_checkpoint
from xsagent.domain.writing.service import ChapterService
from xsagent.storage.project_store import ProjectStore


class CompactionService:
    """每 10 章为更早章节补写结构化 checkpoint（无 LLM，避免阻塞主循环）。"""

    def __init__(self, store: ProjectStore, bible: BibleService, chapters: ChapterService) -> None:
        self._store = store
        self._bible = bible
        self._chapters = chapters
        self._checkpoints = CheckpointStore(bible)

    def maybe_compact(self, project_id: str) -> bool:
        chapter_list = self._chapters.list_chapters(project_id)
        if len(chapter_list) == 0 or len(chapter_list) % 10 != 0:
            return False

        to_compact = chapter_list[:-3]
        for summary in to_compact:
            if self._checkpoints.get(project_id, summary.id):
                continue
            chapter = self._chapters.get_chapter(project_id, summary.id)
            self._checkpoints.put(
                project_id,
                heuristic_checkpoint(
                    summary.id,
                    chapter.content_md,
                    title=chapter.title,
                ),
            )
        run_heuristic_dream(self._bible, self._chapters, project_id)
        return True
