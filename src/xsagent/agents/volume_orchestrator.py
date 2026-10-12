from typing import Awaitable, Callable

from xsagent.agents.orchestrator import WriteChapterOrchestrator
from xsagent.core.exceptions import OutlineNotFoundError
from xsagent.domain.common.spoiler import chapter_number
from xsagent.domain.outline.service import OutlineService
from xsagent.domain.writing.service import ChapterService


class VolumeWriteOrchestrator:
    """用代码保证「写 → 同步/验收」循环，而不是靠 prompt 记住下一步。"""

    def __init__(
        self,
        chapter_orchestrator: WriteChapterOrchestrator,
        chapters: ChapterService,
        outlines: OutlineService,
    ) -> None:
        self._chapter = chapter_orchestrator
        self._chapters = chapters
        self._outlines = outlines

    def select_targets(
        self,
        project_id: str,
        *,
        volume_id: str | None = None,
        limit: int = 3,
    ) -> list[str]:
        start, end = 1, 10_000
        if volume_id:
            volume = self._outlines.get_volume(project_id, volume_id)
            if len(volume.chapter_range) >= 2:
                start, end = int(volume.chapter_range[0]), int(volume.chapter_range[1])
        else:
            summaries = self._chapters.list_chapters(project_id)
            latest_no = chapter_number(summaries[-1].id) if summaries else 1
            end = latest_no + max(limit, 1) + 5

        blueprints = {
            item.chapter_id: item for item in self._outlines.list_chapter_blueprints(project_id)
        }
        existing = {item.id: item for item in self._chapters.list_chapters(project_id)}
        targets: list[str] = []
        for number in range(start, end + 1):
            chapter_id = f"ch_{number:03d}"
            if not self._needs_write(chapter_id, blueprints.get(chapter_id), existing.get(chapter_id)):
                continue
            targets.append(chapter_id)
            if len(targets) >= limit:
                break
        return targets

    def _needs_write(self, chapter_id: str, blueprint, chapter) -> bool:
        del chapter_id
        if blueprint is not None and blueprint.status == "needs_revision":
            return True
        if blueprint is not None and blueprint.status == "completed":
            return False
        if chapter is not None and chapter.word_count >= 30:
            return False
        return True

    async def run(
        self,
        project_id: str,
        instruction: str,
        *,
        volume_id: str | None = None,
        limit: int = 3,
        max_mode: bool | None = None,
        stop_on_revision: bool = True,
        event_cb: Callable[[str, dict], Awaitable[None] | None] | None = None,
    ) -> dict:
        try:
            targets = self.select_targets(project_id, volume_id=volume_id, limit=limit)
        except OutlineNotFoundError:
            raise

        chapter_results: list[dict] = []
        completed: list[str] = []
        stopped_reason = "empty" if not targets else "done"

        for index, chapter_id in enumerate(targets):
            percent = 15 + int(70 * index / max(len(targets), 1))
            await self._emit(
                event_cb,
                "job.progress",
                {
                    "stage": "volume_chapter",
                    "percent": percent,
                    "chapter_id": chapter_id,
                    "index": index + 1,
                    "total": len(targets),
                },
            )
            result = await self._chapter.run(
                project_id,
                instruction,
                chapter_id=chapter_id,
                event_cb=event_cb,
                max_mode=max_mode,
            )
            chapter_results.append(result)
            if result.get("goal_satisfied"):
                completed.append(chapter_id)
            elif stop_on_revision:
                stopped_reason = "goal_failed"
                break

        return {
            "volume_id": volume_id,
            "chapters_attempted": [item["chapter_id"] for item in chapter_results],
            "chapters_completed": completed,
            "stopped_reason": stopped_reason,
            "chapter_results": chapter_results,
            "goal_satisfied": bool(chapter_results) and len(completed) == len(chapter_results),
        }

    async def _emit(
        self,
        event_cb: Callable[[str, dict], Awaitable[None] | None] | None,
        event_type: str,
        payload: dict,
    ) -> None:
        if event_cb is None:
            return
        maybe = event_cb(event_type, payload)
        if hasattr(maybe, "__await__"):
            await maybe
