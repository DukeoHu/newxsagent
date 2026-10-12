import json
from typing import Any

from xsagent.core.exceptions import OutlineNotFoundError, ProjectNotFoundError
from xsagent.domain.outline.models import (
    ChapterBlueprint,
    MasterOutline,
    OutlineBundle,
    VolumeOutline,
)
from xsagent.storage.project_store import ProjectStore, is_macos_metadata


class OutlineService:
    def __init__(self, store: ProjectStore) -> None:
        self._store = store

    def get_bundle(self, project_id: str) -> OutlineBundle:
        self._ensure_project(project_id)
        master = MasterOutline.model_validate(self.get_master(project_id))
        volumes = self.list_volumes(project_id)
        chapters = self.list_chapter_blueprints(project_id)
        completion = self.calculate_completion(project_id)
        master.completion = completion
        return OutlineBundle(
            master=master,
            volumes=volumes,
            chapters=chapters,
            completion=completion,
        )

    def get_master(self, project_id: str) -> dict[str, Any]:
        self._ensure_project(project_id)
        path = self._outlines_dir(project_id) / "master.json"
        data = self._store.read_json(path)
        data["completion"] = self.calculate_completion(project_id)
        return data

    def put_master(self, project_id: str, data: dict[str, Any]) -> dict[str, Any]:
        self._ensure_project(project_id)
        path = self._outlines_dir(project_id) / "master.json"
        current = self._store.read_json(path)
        merged = {**current, **data}
        merged["completion"] = self.calculate_completion(project_id)
        self._store.write_json(path, merged)
        return merged

    def list_volumes(self, project_id: str) -> list[VolumeOutline]:
        self._ensure_project(project_id)
        volumes_dir = self._outlines_dir(project_id) / "volumes"
        results: list[VolumeOutline] = []
        if not volumes_dir.exists():
            return results
        for path in sorted(volumes_dir.glob("*.json")):
            if is_macos_metadata(path):
                continue
            data = self._store.read_json(path)
            data.setdefault("volume_id", path.stem)
            results.append(VolumeOutline.model_validate(data))
        return results

    def get_volume(self, project_id: str, volume_id: str) -> VolumeOutline:
        path = self._outlines_dir(project_id) / "volumes" / f"{volume_id}.json"
        if not path.exists():
            raise OutlineNotFoundError(f"volumes/{volume_id}")
        data = self._store.read_json(path)
        data.setdefault("volume_id", volume_id)
        return VolumeOutline.model_validate(data)

    def put_volume(self, project_id: str, volume_id: str, data: dict[str, Any]) -> VolumeOutline:
        self._ensure_project(project_id)
        path = self._outlines_dir(project_id) / "volumes" / f"{volume_id}.json"
        current: dict[str, Any] = {}
        if path.exists():
            current = self._store.read_json(path)
        merged = {**current, **data, "volume_id": volume_id}
        self._store.write_json(path, merged)
        return VolumeOutline.model_validate(merged)

    def list_chapter_blueprints(self, project_id: str) -> list[ChapterBlueprint]:
        self._ensure_project(project_id)
        chapters_dir = self._outlines_dir(project_id) / "chapters"
        results: list[ChapterBlueprint] = []
        if not chapters_dir.exists():
            return results
        for path in sorted(chapters_dir.glob("*.json")):
            if is_macos_metadata(path):
                continue
            data = self._store.read_json(path)
            data.setdefault("chapter_id", path.stem)
            results.append(ChapterBlueprint.model_validate(data))
        return results

    def get_chapter_blueprint(self, project_id: str, chapter_id: str) -> ChapterBlueprint:
        path = self._outlines_dir(project_id) / "chapters" / f"{chapter_id}.json"
        if not path.exists():
            raise OutlineNotFoundError(f"chapters/{chapter_id}")
        data = self._store.read_json(path)
        data.setdefault("chapter_id", chapter_id)
        return ChapterBlueprint.model_validate(data)

    def put_chapter_blueprint(
        self, project_id: str, chapter_id: str, data: dict[str, Any]
    ) -> ChapterBlueprint:
        self._ensure_project(project_id)
        path = self._outlines_dir(project_id) / "chapters" / f"{chapter_id}.json"
        current: dict[str, Any] = {}
        if path.exists():
            current = self._store.read_json(path)
        merged = {**current, **data, "chapter_id": chapter_id}
        self._store.write_json(path, merged)
        return ChapterBlueprint.model_validate(merged)

    def calculate_completion(self, project_id: str) -> float:
        blueprints = self.list_chapter_blueprints(project_id)
        if not blueprints:
            written = len(self._store.list_chapters(project_id))
            return 100.0 if written > 0 else 0.0
        completed = sum(1 for bp in blueprints if bp.status == "completed")
        return round(completed / len(blueprints) * 100, 1)

    def _outlines_dir(self, project_id: str):
        return self._store.project_path(project_id) / "outlines"

    def _ensure_project(self, project_id: str) -> None:
        if not self._store.exists(project_id):
            raise ProjectNotFoundError(project_id)
