from datetime import UTC, datetime
from typing import Awaitable, Callable

from xsagent.agents.checkpoint_writer import CheckpointWriter
from xsagent.agents.context import WritingContextBuilder
from xsagent.agents.explore import ExploreAgent
from xsagent.agents.goal import GoalVerifier
from xsagent.agents.prose import ProseAgent
from xsagent.agents.reviewer import ReviewerAgent
from xsagent.domain.action_log.service import ActionLogService
from xsagent.domain.memory.patch_engine import PatchEngine
from xsagent.domain.memory.patch_models import BiblePatch, RiskLevel
from xsagent.domain.memory.service import BibleService
from xsagent.domain.outline.service import OutlineService
from xsagent.domain.project.models import InterventionLevel
from xsagent.domain.project.service import ProjectService
from xsagent.domain.quality.goal import GoalVerdict
from xsagent.domain.quality.models import PendingItem, PendingItemStatus
from xsagent.domain.quality.pending_service import PendingService
from xsagent.domain.quality.risk import should_auto_apply
from xsagent.domain.writing.compaction import CompactionService
from xsagent.domain.writing.service import ChapterService
from xsagent.storage.snapshot_service import SnapshotService

GOAL_REWRITE_LIMIT = 1


class WriteChapterOrchestrator:
    def __init__(
        self,
        projects: ProjectService,
        chapters: ChapterService,
        bible: BibleService,
        outlines: OutlineService,
        patch_engine: PatchEngine,
        prose: ProseAgent,
        reviewer: ReviewerAgent,
        goal: GoalVerifier,
        checkpoint_writer: CheckpointWriter,
        context_builder: WritingContextBuilder,
        action_log: ActionLogService,
        pending: PendingService,
        snapshots: SnapshotService,
        compaction: CompactionService,
        explore: ExploreAgent | None = None,
        *,
        goal_rewrite_limit: int = GOAL_REWRITE_LIMIT,
    ) -> None:
        self._projects = projects
        self._chapters = chapters
        self._bible = bible
        self._outlines = outlines
        self._patch_engine = patch_engine
        self._prose = prose
        self._reviewer = reviewer
        self._goal = goal
        self._checkpoint_writer = checkpoint_writer
        self._context = context_builder
        self._action_log = action_log
        self._pending = pending
        self._snapshots = snapshots
        self._compaction = compaction
        self._explore = explore
        self._goal_rewrite_limit = goal_rewrite_limit

    async def run(
        self,
        project_id: str,
        instruction: str,
        chapter_id: str | None = None,
        event_cb: Callable[[str, dict], Awaitable[None] | None] | None = None,
        max_mode: bool | None = None,
    ) -> dict:
        project = self._projects.get_project(project_id)
        target_id = self._chapters.resolve_chapter_id(project_id, chapter_id)

        await self._emit(event_cb, "job.progress", {"stage": "snapshot", "percent": 10})
        self._snapshots.create(project_id, label=f"pre-write-{target_id}")

        content_md = ""
        chapter = None
        ctx: dict = {}
        verdict = GoalVerdict(satisfied=True, summary="未执行验收")
        rewrite_count = 0
        goal_feedback = "（无）"
        selected_plan = "（无）"
        max_mode_used = False

        preview = self._context.build(project, target_id, instruction)
        role = str(preview.get("chapter_role") or "")
        if max_mode is True or (max_mode is None and role == "payoff"):
            max_mode_used = True
            if self._explore is not None:
                await self._emit(event_cb, "job.progress", {"stage": "max_mode", "percent": 18})
                plan = await self._explore.select_plan(
                    chapter_id=target_id,
                    prompt=instruction,
                    context=preview,
                )
                selected_plan = (
                    f"{plan.title}\n{plan.summary}\n"
                    + "\n".join(f"- {beat}" for beat in plan.beats)
                )

        while True:
            ctx = self._context.build(project, target_id, instruction)
            ctx["goal_feedback"] = goal_feedback
            ctx["selected_plan"] = selected_plan
            await self._emit(
                event_cb,
                "job.progress",
                {
                    "stage": "writing" if rewrite_count == 0 else "rewrite",
                    "percent": 25 if rewrite_count == 0 else 40,
                    "rewrite_count": rewrite_count,
                },
            )
            chunks: list[str] = []
            async for chunk in self._prose.stream(ctx):
                chunks.append(chunk)
                await self._emit(event_cb, "job.chunk", {"chunk": chunk})
            content_md = "".join(chunks)
            chapter = self._chapters.save_generated(project_id, target_id, content_md)

            await self._emit(event_cb, "job.progress", {"stage": "goal_verify", "percent": 50})
            verdict = await self._goal.verify(
                chapter_id=target_id,
                content=content_md,
                word_count=chapter.word_count,
                words_per_chapter=int(ctx.get("words_per_chapter") or 3000),
                beats=list(ctx.get("beats") or []),
                dormant_threads=list(ctx.get("dormant_threads") or []),
                forbidden_reveals=list(ctx.get("forbidden_reveals") or []),
                hard_constraints=str(ctx.get("hard_constraints") or ""),
                chapter_mandate=str(ctx.get("chapter_mandate") or ""),
            )
            if verdict.satisfied or verdict.impossible or rewrite_count >= self._goal_rewrite_limit:
                break
            rewrite_count += 1
            goal_feedback = verdict.feedback_text()

        assert chapter is not None

        self._action_log.append(
            project_id,
            action_type="write.chapter",
            diff_summary=f"生成章节 {target_id}（{chapter.word_count} 字）",
            metadata={
                "chapter_id": target_id,
                "rewrite_count": rewrite_count,
                "goal_satisfied": verdict.satisfied,
            },
        )

        await self._emit(event_cb, "job.progress", {"stage": "checkpoint", "percent": 52})
        await self._checkpoint_writer.write(project_id, target_id, content_md)

        pending_ids: list[str] = []
        if not verdict.satisfied:
            item = self._create_pending(
                project_id,
                item_type="goal_gap",
                risk=RiskLevel.HIGH if verdict.impossible else RiskLevel.MEDIUM,
                summary=verdict.feedback_text(),
            )
            pending_ids.append(item.id)
            self._action_log.append(
                project_id,
                action_type="goal_gap.pending",
                diff_summary=item.summary,
                metadata={"pending_id": item.id, "impossible": verdict.impossible},
            )

        await self._emit(event_cb, "job.progress", {"stage": "sync_bible", "percent": 55})
        sync_patch = await self._reviewer.sync_bible(target_id, content_md)
        sync_apply, sync_pending = self._route_patch(
            project_id, project.intervention_level, sync_patch, item_type="bible_sync"
        )
        pending_ids.extend(sync_pending)

        await self._emit(event_cb, "job.progress", {"stage": "drift_detect", "percent": 70})
        drift = await self._reviewer.detect_drift(target_id, content_md, ctx["bible_summary"])
        for finding in drift.findings:
            if finding.suggested_patch:
                _, finding_pending = self._route_patch(
                    project_id,
                    project.intervention_level,
                    finding.suggested_patch,
                    item_type="drift_fix",
                    summary=finding.description,
                    finding_id=finding.id,
                )
                pending_ids.extend(finding_pending)
            elif finding.severity == RiskLevel.HIGH:
                item = self._create_pending(
                    project_id,
                    item_type="drift_finding",
                    risk=finding.severity,
                    summary=finding.description,
                    finding=finding,
                )
                pending_ids.append(item.id)

        blueprint_status = "completed" if verdict.satisfied else "needs_revision"
        self._outlines.put_chapter_blueprint(
            project_id,
            target_id,
            {"title": chapter.title, "status": blueprint_status},
        )

        await self._emit(event_cb, "job.progress", {"stage": "compaction", "percent": 90})
        compacted = self._compaction.maybe_compact(project_id)
        if compacted:
            self._action_log.append(
                project_id,
                action_type="compaction",
                diff_summary="已补写较早章节的结构化状态记录",
            )

        actions = self._action_log.list_entries(project_id, limit=10)
        action_types = [a.action_type for a in actions]

        return {
            "chapter_id": target_id,
            "word_count": chapter.word_count,
            "sync_patch": sync_patch,
            "sync_apply": sync_apply,
            "drift_findings_count": len(drift.findings),
            "pending_ids": pending_ids,
            "compacted": compacted,
            "actions_logged": action_types,
            "goal_satisfied": verdict.satisfied,
            "goal_impossible": verdict.impossible,
            "goal_summary": verdict.summary,
            "blueprint_status": blueprint_status,
            "rewrite_count": rewrite_count,
            "checkpointed": True,
            "max_mode_used": max_mode_used,
            "selected_plan": selected_plan if max_mode_used else "",
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

    def _route_patch(
        self,
        project_id: str,
        intervention: InterventionLevel,
        patch: BiblePatch,
        *,
        item_type: str,
        summary: str | None = None,
        finding_id: str | None = None,
    ) -> tuple:
        if not patch.updates:
            return None, []

        if should_auto_apply(intervention, patch.risk_level):
            try:
                result = self._patch_engine.apply(project_id, patch)
            except Exception as exc:  # noqa: BLE001
                item = self._create_pending(
                    project_id,
                    item_type=item_type,
                    risk=RiskLevel.MEDIUM,
                    summary=f"自动同步失败，待人工确认：{exc}",
                    patch=patch,
                )
                self._action_log.append(
                    project_id,
                    action_type=f"{item_type}.pending",
                    diff_summary=item.summary,
                    metadata={
                        "pending_id": item.id,
                        "apply_error": str(exc),
                        "finding_id": finding_id,
                    },
                )
                return None, [item.id]
            self._action_log.append(
                project_id,
                action_type=f"{item_type}.apply",
                diff_summary=patch.explanation or summary or "自动应用 Patch",
                metadata={"risk_level": patch.risk_level.value, "finding_id": finding_id},
            )
            return result, []

        item = self._create_pending(
            project_id,
            item_type=item_type,
            risk=patch.risk_level,
            summary=summary or patch.explanation,
            patch=patch,
        )
        self._action_log.append(
            project_id,
            action_type=f"{item_type}.pending",
            diff_summary=item.summary,
            metadata={"pending_id": item.id, "risk_level": patch.risk_level.value},
        )
        return None, [item.id]

    def _create_pending(
        self,
        project_id: str,
        *,
        item_type: str,
        risk: RiskLevel,
        summary: str,
        patch: BiblePatch | None = None,
        finding=None,
    ) -> PendingItem:
        item = PendingItem(
            project_id=project_id,
            item_type=item_type,
            risk_level=risk,
            status=PendingItemStatus.PENDING,
            patch=patch,
            finding=finding,
            created_at=datetime.now(UTC).isoformat(),
            summary=summary,
        )
        return self._pending.add(item)
