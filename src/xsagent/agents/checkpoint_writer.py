from pydantic import ValidationError

from xsagent.agents.prompts.checkpoint import CHECKPOINT_SYSTEM, CHECKPOINT_TEMPLATE
from xsagent.domain.writing.checkpoint import (
    ChapterCheckpoint,
    CheckpointStore,
    heuristic_checkpoint,
    render_checkpoint,
    take_ending_slice,
)
from xsagent.domain.writing.service import ChapterService
from xsagent.llm.base import LLMProvider, LLMRequest, LLMTask
from xsagent.llm.parse import parse_llm_json


class CheckpointWriter:
    """独立于写作者的结构化记忆写入器；主循环只读。"""

    def __init__(
        self,
        llm: LLMProvider,
        store: CheckpointStore,
        chapters: ChapterService,
    ) -> None:
        self._llm = llm
        self._store = store
        self._chapters = chapters

    async def write(self, project_id: str, chapter_id: str, content_md: str) -> ChapterCheckpoint:
        previous = self._previous_text(project_id, chapter_id)
        prompt = CHECKPOINT_TEMPLATE.format(
            chapter_id=chapter_id,
            previous_checkpoint=previous,
            content=content_md,
        )
        try:
            raw = await self._llm.generate(
                LLMRequest(
                    task=LLMTask.CHECKPOINT,
                    system=CHECKPOINT_SYSTEM,
                    prompt=prompt,
                    json_mode=True,
                )
            )
            data = parse_llm_json(raw)
            title = ""
            try:
                title = self._chapters.get_chapter(project_id, chapter_id).title
            except Exception:
                title = chapter_id
            checkpoint = ChapterCheckpoint.model_validate(
                {
                    **data,
                    "chapter_id": chapter_id,
                    "ending_slice": take_ending_slice(content_md),
                    "intent": data.get("intent") or title,
                    "summary": data.get("summary") or "",
                }
            )
            if not checkpoint.summary:
                checkpoint = heuristic_checkpoint(chapter_id, content_md, title=title)
                checkpoint.intent = str(data.get("intent") or checkpoint.intent)
                checkpoint.next_action = str(data.get("next_action") or "")
        except (ValueError, TypeError, ValidationError):
            title = chapter_id
            try:
                title = self._chapters.get_chapter(project_id, chapter_id).title
            except Exception:
                pass
            checkpoint = heuristic_checkpoint(chapter_id, content_md, title=title)

        return self._store.put(project_id, checkpoint)

    def _previous_text(self, project_id: str, chapter_id: str) -> str:
        checkpoints = self._store.get_all(project_id)
        prior = [
            item
            for item in checkpoints.values()
            if item.chapter_id != chapter_id
        ]
        prior.sort(key=lambda item: item.chapter_id)
        if not prior:
            return "（无）"
        return render_checkpoint(prior[-1])
