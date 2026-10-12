from typing import Any

from xsagent.core.exceptions import BibleSectionNotFoundError, ProjectNotFoundError
from xsagent.domain.common.paths import assert_locked_fields_unchanged
from xsagent.domain.common.text import bible_sections, is_valid_bible_section
from xsagent.storage.project_store import ProjectStore


class BibleService:
    def __init__(self, store: ProjectStore) -> None:
        self._store = store

    def list_sections(self, project_id: str) -> list[str]:
        self._ensure_project(project_id)
        return bible_sections()

    def get_section(self, project_id: str, section: str) -> dict[str, Any]:
        self._ensure_section(project_id, section)
        return self._store.read_json(self._section_path(project_id, section))

    def put_section(self, project_id: str, section: str, data: dict[str, Any]) -> dict[str, Any]:
        self._ensure_section(project_id, section)
        path = self._section_path(project_id, section)
        current = self._store.read_json(path)
        locked = current.get("locked_fields", [])
        if locked:
            assert_locked_fields_unchanged(current, data, locked)
        if "locked_fields" not in data:
            data["locked_fields"] = locked
        self._store.write_json(path, data)
        return data

    def update_locked_fields(
        self, project_id: str, section: str, locked_fields: list[str]
    ) -> dict[str, Any]:
        self._ensure_section(project_id, section)
        path = self._section_path(project_id, section)
        data = self._store.read_json(path)
        data["locked_fields"] = locked_fields
        self._store.write_json(path, data)
        return data

    def _section_path(self, project_id: str, section: str):
        return self._store.project_path(project_id) / "story_bible" / f"{section}.json"

    def _ensure_project(self, project_id: str) -> None:
        if not self._store.exists(project_id):
            raise ProjectNotFoundError(project_id)

    def _ensure_section(self, project_id: str, section: str) -> None:
        self._ensure_project(project_id)
        if not is_valid_bible_section(section):
            raise BibleSectionNotFoundError(section)
