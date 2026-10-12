import copy
from typing import Any

from xsagent.core.exceptions import BibleSectionNotFoundError, FieldLockedError
from xsagent.domain.common.paths import (
    append_nested_value,
    assert_locked_fields_unchanged,
    get_nested_value,
    set_nested_value,
)
from xsagent.domain.common.text import is_valid_bible_section
from xsagent.domain.memory.patch_models import BiblePatch, PatchApplyResult, PatchPreview, PatchUpdate, RiskLevel
from xsagent.domain.memory.service import BibleService


class PatchEngine:
    def __init__(self, bible: BibleService) -> None:
        self._bible = bible

    def preview(self, project_id: str, patch: BiblePatch) -> list[PatchPreview]:
        previews: list[PatchPreview] = []
        sections = self._group_by_section(patch.updates)
        for section, updates in sections.items():
            before = copy.deepcopy(self._bible.get_section(project_id, section))
            after = copy.deepcopy(before)
            self._apply_updates_to_data(after, updates)
            changed = self._diff_paths(before, after, updates)
            previews.append(
                PatchPreview(section=section, before=before, after=after, changed_paths=changed)
            )
        return previews

    def apply(
        self,
        project_id: str,
        patch: BiblePatch,
        *,
        force: bool = False,
    ) -> PatchApplyResult:
        previews = self.preview(project_id, patch)
        for preview in previews:
            locked = preview.before.get("locked_fields", [])
            if locked and not force:
                assert_locked_fields_unchanged(preview.before, preview.after, locked)

        for preview in previews:
            self._bible.put_section(project_id, preview.section, preview.after)

        return PatchApplyResult(
            applied=True,
            previews=previews,
            risk_level=patch.risk_level,
            explanation=patch.explanation,
            auto_applied=True,
        )

    def _group_by_section(self, updates: list[PatchUpdate]) -> dict[str, list[PatchUpdate]]:
        grouped: dict[str, list[PatchUpdate]] = {}
        for update in updates:
            section = self._normalize_section(update.section)
            if not is_valid_bible_section(section):
                raise BibleSectionNotFoundError(update.section)
            path = self._normalize_path(update.path, section)
            normalized = update.model_copy(update={"section": section, "path": path})
            grouped.setdefault(section, []).append(normalized)
        return grouped

    def _apply_updates_to_data(self, data: dict[str, Any], updates: list[PatchUpdate]) -> None:
        for update in updates:
            if update.op == "append":
                append_nested_value(data, update.path, update.value)
            elif update.op == "merge" and isinstance(update.value, dict):
                if not update.path:
                    data.update(update.value)
                    continue
                target = get_nested_value(data, update.path)
                if isinstance(target, dict):
                    target.update(update.value)
                else:
                    raise TypeError(f"merge requires dict at path: {update.path}")
            else:
                if not update.path:
                    if not isinstance(update.value, dict):
                        raise TypeError("set with empty path requires dict value")
                    data.clear()
                    data.update(update.value)
                    continue
                set_nested_value(data, update.path, update.value)

    def _diff_paths(
        self, before: dict[str, Any], after: dict[str, Any], updates: list[PatchUpdate]
    ) -> list[str]:
        paths: list[str] = []
        for update in updates:
            key = f"{update.section}.{update.path}"
            if key not in paths:
                paths.append(key)
        return paths

    def _normalize_section(self, section: str) -> str:
        normalized = section.strip()
        if is_valid_bible_section(normalized):
            return normalized
        candidate = normalized.strip("/").split("/")[-1].split(".")[-1]
        return candidate

    def _normalize_path(self, path: str, section: str) -> str:
        raw = path.strip()
        normalized = raw.replace("\\", "/").replace("/", ".").lstrip(".")
        if not normalized:
            return ""
        if normalized == section and (raw.startswith("/") or "/" in raw):
            return ""
        if raw.startswith("/") or "/" in raw:
            prefix = f"{section}."
            if normalized.startswith(prefix):
                return normalized[len(prefix) :]
        return normalized
