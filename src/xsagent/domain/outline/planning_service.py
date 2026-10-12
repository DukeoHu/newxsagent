import json
from typing import Any

from xsagent.agents.outline_planner import OutlinePlannerAgent
from xsagent.domain.common.scope import (
    find_volume_for_chapter,
    scoped_context_for_chapter,
    volume_scope_text,
)
from xsagent.domain.common.spoiler import (
    bible_summary_text,
    chapter_number,
    spoiler_guard_for_chapter,
    spoiler_safe_bible_sections,
)
from xsagent.domain.common.text import bible_sections
from xsagent.domain.memory.service import BibleService
from xsagent.domain.narrative.hard_constraints import (
    hard_constraints_from_mandate,
    scrub_beats_against_hard_constraints,
)
from xsagent.domain.narrative.mandate import ChapterMandateBuilder
from xsagent.domain.narrative.normalize import (
    normalize_volume_threads,
    volume_has_usable_threads,
)
from xsagent.domain.outline.service import OutlineService
from xsagent.domain.project.service import ProjectService
from xsagent.llm.context import llm_call_context

CHAPTER_BATCH_SIZE = 5


def chapter_id_from_number(no: int) -> str:
    return f"ch_{no:03d}"


class OutlinePlanningService:
    def __init__(
        self,
        projects: ProjectService,
        bible: BibleService,
        outlines: OutlineService,
        agent: OutlinePlannerAgent,
    ) -> None:
        self._projects = projects
        self._bible = bible
        self._outlines = outlines
        self._agent = agent
        self._mandate_builder = ChapterMandateBuilder()

    async def generate_master(self, project_id: str, *, apply: bool = True) -> dict:
        with llm_call_context(project_id=project_id):
            return await self._generate_master(project_id, apply=apply)

    async def _generate_master(self, project_id: str, *, apply: bool = True) -> dict:
        project = self._projects.get_project(project_id)
        bundle = self._outlines.get_bundle(project_id)
        total_chapters = max(1, len(bundle.chapters))
        volume_count = max(1, len(bundle.volumes))

        result = await self._agent.generate_master(
            project_name=project.name,
            genre=project.genre,
            bible_summary=self._bible_summary(project_id),
            current_master=bundle.master.model_dump(),
            total_chapters=total_chapters,
            volume_count=volume_count,
        )

        if apply:
            master = result.get("master", {})
            if master:
                self._outlines.put_master(project_id, master)
            for vol in result.get("volumes", []):
                volume_id = vol.get("volume_id")
                if not volume_id:
                    continue
                threads = normalize_volume_threads(vol, genre=project.genre)
                self._outlines.put_volume(
                    project_id,
                    volume_id,
                    {
                        "title": vol.get("title", volume_id),
                        "arcs": vol.get("arcs", []),
                        "arc_phases": vol.get("arc_phases", []),
                        "chapter_range": vol.get("chapter_range", []),
                        "stage_goal": vol.get("stage_goal", ""),
                        "opening_focus": vol.get("opening_focus", ""),
                        "threads": threads,
                        "allowed_knowledge": vol.get("allowed_knowledge", []),
                        "opening_knowledge": vol.get("opening_knowledge", []),
                        "forbidden_reveals": vol.get("forbidden_reveals", []),
                        "knowledge_ceiling": vol.get("knowledge_ceiling", ""),
                        "foreshadowing_plants": vol.get("foreshadowing_plants", []),
                    },
                )
        else:
            for vol in result.get("volumes", []):
                vol["threads"] = normalize_volume_threads(vol, genre=project.genre)
        return result

    async def generate_threads(
        self,
        project_id: str,
        *,
        only_missing: bool = True,
        apply: bool = True,
    ) -> dict:
        """用 AI 为各卷自动生成 / 补全叙事线程。"""
        with llm_call_context(project_id=project_id):
            return await self._generate_threads(
                project_id,
                only_missing=only_missing,
                apply=apply,
            )

    async def _generate_threads(
        self,
        project_id: str,
        *,
        only_missing: bool = True,
        apply: bool = True,
    ) -> dict:
        project = self._projects.get_project(project_id)
        volumes = [volume.model_dump() for volume in self._outlines.list_volumes(project_id)]
        targets = [
            {
                "volume_id": vol.get("volume_id"),
                "title": vol.get("title"),
                "chapter_range": vol.get("chapter_range"),
                "stage_goal": vol.get("stage_goal"),
                "arcs": vol.get("arcs", []),
            }
            for vol in volumes
            if vol.get("volume_id")
            and (not only_missing or not volume_has_usable_threads(vol))
        ]
        if not targets:
            return {"volumes": [], "applied": 0, "skipped": len(volumes)}

        result = await self._agent.generate_threads(
            project_name=project.name,
            genre=project.genre,
            bible_summary=self._bible_summary(project_id),
            volumes=targets,
        )
        generated = result.get("volumes", [])
        by_id = {
            item.get("volume_id"): item
            for item in generated
            if isinstance(item, dict) and item.get("volume_id")
        }

        applied: list[dict] = []
        for target in targets:
            volume_id = target["volume_id"]
            current = self._outlines.get_volume(project_id, volume_id).model_dump()
            llm_item = by_id.get(volume_id, {})
            merged = {
                **current,
                "opening_focus": llm_item.get("opening_focus")
                or current.get("opening_focus")
                or "",
                "threads": llm_item.get("threads") or current.get("threads") or [],
            }
            threads = normalize_volume_threads(merged, genre=project.genre)
            payload = {
                "opening_focus": merged["opening_focus"],
                "threads": threads,
            }
            if apply:
                self._outlines.put_volume(project_id, volume_id, payload)
            applied.append({"volume_id": volume_id, "threads": threads})

        return {
            "volumes": applied,
            "applied": len(applied) if apply else 0,
            "skipped": len(volumes) - len(targets),
        }

    async def ensure_volume_threads(self, project_id: str, volume_id: str) -> dict:
        """蓝图/写作前确保该卷有可用 threads；缺失时自动 AI 生成。"""
        volume = self._outlines.get_volume(project_id, volume_id).model_dump()
        if volume_has_usable_threads(volume):
            threads = normalize_volume_threads(
                volume, genre=self._projects.get_project(project_id).genre
            )
            if threads != volume.get("threads"):
                self._outlines.put_volume(project_id, volume_id, {"threads": threads})
            return {"volume_id": volume_id, "threads": threads, "generated": False}

        result = await self.generate_threads(
            project_id, only_missing=True, apply=True
        )
        refreshed = self._outlines.get_volume(project_id, volume_id).model_dump()
        return {
            "volume_id": volume_id,
            "threads": refreshed.get("threads", []),
            "generated": True,
            "batch": result,
        }

    async def generate_chapters(
        self,
        project_id: str,
        chapter_ids: list[str],
        *,
        apply: bool = True,
    ) -> dict:
        with llm_call_context(project_id=project_id):
            return await self._generate_chapters(
                project_id,
                chapter_ids,
                apply=apply,
            )

    async def _generate_chapters(
        self,
        project_id: str,
        chapter_ids: list[str],
        *,
        apply: bool = True,
    ) -> dict:
        if not chapter_ids:
            return {"chapters": [], "applied": 0}

        project = self._projects.get_project(project_id)
        master = self._outlines.get_master(project_id)
        bundle = self._outlines.get_bundle(project_id)
        total_chapters = max(1, len(bundle.chapters))
        all_generated: list[dict[str, Any]] = []

        sorted_ids = sorted(chapter_ids, key=chapter_number)
        sections_data = {
            section: self._bible.get_section(project_id, section)
            for section in bible_sections()
        }
        plot_section = sections_data.get("plot", {})
        characters_section = sections_data.get("characters", {})

        # 蓝图生成前：缺失叙事线程则自动 AI 补全
        volumes_all = [volume.model_dump() for volume in self._outlines.list_volumes(project_id)]
        ensured_volume_ids: set[str] = set()
        for cid in sorted_ids:
            volume = find_volume_for_chapter(volumes_all, chapter_number(cid))
            volume_id = (volume or {}).get("volume_id")
            if volume_id and volume_id not in ensured_volume_ids:
                await self.ensure_volume_threads(project_id, volume_id)
                ensured_volume_ids.add(volume_id)
                volumes_all = [
                    volume.model_dump() for volume in self._outlines.list_volumes(project_id)
                ]

        for i in range(0, len(sorted_ids), CHAPTER_BATCH_SIZE):
            batch = sorted_ids[i : i + CHAPTER_BATCH_SIZE]
            batch_start = chapter_number(batch[0])
            neighbor = self._neighbor_context(project_id, batch)
            volumes = volumes_all
            volume = find_volume_for_chapter(volumes, batch_start)
            spoiler_guard = spoiler_guard_for_chapter(
                batch_start,
                total_chapters=total_chapters,
            )
            chapter_mandates = self._mandate_builder.build_batch_json(
                batch,
                volume=volume,
                plot_section=plot_section,
                characters_section=characters_section,
                chapter_number_fn=chapter_number,
            )
            volume_scope = volume_scope_text(volume, batch_start) if volume else "{}"
            scoped_context = self._scoped_context_for_chapter(
                project_id,
                batch_start,
                volume=volume,
                master_acts=list(master.get("acts", [])),
            )

            result = await self._agent.generate_chapter_batch(
                project_name=project.name,
                genre=project.genre,
                chapter_mandates=chapter_mandates,
                volume_scope=volume_scope,
                scoped_context=scoped_context,
                chapter_ids=batch,
                neighbor_context=neighbor,
                spoiler_guard=spoiler_guard,
            )
            chapters = result.get("chapters", [])
            mandates_by_id = {
                cid: self._mandate_builder.build(
                    chapter_id=cid,
                    chapter_no=chapter_number(cid),
                    volume=volume,
                    plot_section=plot_section,
                    characters_section=characters_section,
                )
                for cid in batch
            }
            normalized = self._normalize_chapters(batch, chapters, mandates_by_id)
            all_generated.extend(normalized)

            if apply:
                for item in normalized:
                    self._outlines.put_chapter_blueprint(project_id, item["chapter_id"], item)

        return {"chapters": all_generated, "applied": len(all_generated) if apply else 0}

    async def generate_volume(
        self,
        project_id: str,
        volume_id: str,
        *,
        only_pending: bool = True,
        apply: bool = True,
    ) -> dict:
        volume = self._outlines.get_volume(project_id, volume_id)
        chapter_ids = self._chapter_ids_for_volume(volume.chapter_range)
        if only_pending:
            chapter_ids = self._filter_pending(project_id, chapter_ids)
        return await self.generate_chapters(project_id, chapter_ids, apply=apply)

    async def generate_all(
        self,
        project_id: str,
        *,
        only_pending: bool = True,
        apply: bool = True,
        regenerate_master: bool = False,
    ) -> dict:
        bundle = self._outlines.get_bundle(project_id)
        master_result = None
        if regenerate_master or not bundle.master.acts:
            master_result = await self.generate_master(project_id, apply=apply)

        volumes = self._outlines.list_volumes(project_id)
        volume_results: list[dict] = []
        total_applied = 0
        all_chapters: list[dict] = []

        for volume in volumes:
            result = await self.generate_volume(
                project_id,
                volume.volume_id,
                only_pending=only_pending,
                apply=apply,
            )
            volume_results.append(
                {
                    "volume_id": volume.volume_id,
                    "applied": result.get("applied", 0),
                }
            )
            total_applied += result.get("applied", 0)
            all_chapters.extend(result.get("chapters", []))

        if not volumes and bundle.chapters:
            chapter_ids = [ch.chapter_id for ch in bundle.chapters]
            if only_pending:
                chapter_ids = self._filter_pending(project_id, chapter_ids)
            result = await self.generate_chapters(project_id, chapter_ids, apply=apply)
            total_applied = result.get("applied", 0)
            all_chapters = result.get("chapters", [])

        return {
            "master": master_result,
            "volumes": volume_results,
            "chapters": all_chapters,
            "applied": total_applied,
        }

    async def recommend_chapter(self, project_id: str, chapter_id: str) -> dict:
        result = await self.generate_chapters(project_id, [chapter_id], apply=False)
        chapters = result.get("chapters", [])
        if not chapters:
            raise ValueError(f"未能生成章节蓝图：{chapter_id}")
        return chapters[0]

    def _bible_summary(self, project_id: str) -> str:
        return self._spoiler_safe_bible_summary(project_id, chapter_no=1)

    def _spoiler_safe_bible_summary(
        self,
        project_id: str,
        chapter_no: int,
        *,
        master_acts: list[dict] | None = None,
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

    def _scoped_context_for_chapter(
        self,
        project_id: str,
        chapter_no: int,
        *,
        volume: dict[str, Any] | None,
        master_acts: list[dict] | None = None,
    ) -> str:
        sections = {
            section: self._bible.get_section(project_id, section)
            for section in bible_sections()
        }
        return scoped_context_for_chapter(
            bible_sections=sections,
            volume=volume,
            chapter_no=chapter_no,
            master_acts=master_acts,
        )

    def _chapter_ids_for_volume(self, chapter_range: list[int]) -> list[str]:
        if len(chapter_range) < 2:
            return []
        start, end = chapter_range[0], chapter_range[1]
        return [chapter_id_from_number(n) for n in range(start, end + 1)]

    def _filter_pending(self, project_id: str, chapter_ids: list[str]) -> list[str]:
        pending: list[str] = []
        for cid in chapter_ids:
            try:
                bp = self._outlines.get_chapter_blueprint(project_id, cid)
            except Exception:
                pending.append(cid)
                continue
            if not bp.beats or bp.status == "pending":
                pending.append(cid)
        return pending

    def _neighbor_context(self, project_id: str, batch: list[str]) -> str:
        if not batch:
            return ""
        first_no = chapter_number(batch[0])
        last_no = chapter_number(batch[-1])
        neighbors: list[dict] = []
        for no in range(max(1, first_no - 2), last_no + 1):
            cid = chapter_id_from_number(no)
            if cid in batch:
                continue
            try:
                bp = self._outlines.get_chapter_blueprint(project_id, cid)
                if bp.beats:
                    neighbors.append(bp.model_dump())
            except Exception:
                continue
        return json.dumps(neighbors, ensure_ascii=False)

    def _normalize_chapters(
        self,
        expected_ids: list[str],
        generated: list[dict],
        mandates_by_id: dict | None = None,
    ) -> list[dict[str, Any]]:
        by_id = {item.get("chapter_id"): item for item in generated if item.get("chapter_id")}
        normalized: list[dict[str, Any]] = []
        mandates_by_id = mandates_by_id or {}
        for cid in expected_ids:
            item = by_id.get(cid, {})
            mandate = mandates_by_id.get(cid)
            no = chapter_number(cid)
            beats = item.get("beats") or [
                f"承接前文，推进第{no}章主线",
                "抬升冲突或引入新线索（早期章节禁止提前揭晓后期谜底）",
                "章末留钩子",
            ]
            if mandate and mandate.dormant_threads:
                dormant_labels = "、".join(mandate.dormant_threads)
                beats = item.get("beats") or [
                    f"推进{mandate.primary_thread}相关日常与悬念",
                    f"以下线程本章休眠不得推进：{dormant_labels}",
                    "章末留钩子",
                ]
            hard = (
                hard_constraints_from_mandate(mandate)
                if mandate
                else (item.get("hard_constraints") or {})
            )
            if hard:
                beats, _conflicts = scrub_beats_against_hard_constraints(list(beats), hard)
            soft = item.get("constraints") or [
                "保持人物动机一致",
                "不破坏已锁定设定",
            ]
            normalized.append(
                {
                    "chapter_id": cid,
                    "title": item.get("title") or f"第{no}章",
                    "beats": beats,
                    "constraints": soft,
                    "hard_constraints": hard,
                    "author_notes": item.get("author_notes") or "",
                    "chapter_role": item.get("chapter_role")
                    or (mandate.chapter_role if mandate else "bridge"),
                    "primary_thread": item.get("primary_thread")
                    or (mandate.primary_thread if mandate else "main"),
                    "dormant_threads": item.get("dormant_threads")
                    or (mandate.dormant_threads if mandate else []),
                    "status": item.get("status", "ready"),
                }
            )
        return normalized
