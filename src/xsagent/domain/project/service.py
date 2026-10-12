import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import yaml

from xsagent.core.exceptions import ProjectAlreadyExistsError, ProjectNotFoundError
from xsagent.domain.project.models import (
    HealthScore,
    InterventionLevel,
    Project,
    ProjectCreate,
    ProjectStatus,
    ProjectUpdate,
)
from xsagent.storage.project_store import ProjectStore, is_macos_metadata

_PLACEHOLDER_PATTERN = re.compile(r"\{\{(\w+)\}\}")


class ProjectService:
    def __init__(self, store: ProjectStore, template_dir: Path) -> None:
        self._store = store
        self._template_dir = template_dir

    def list_projects(self) -> list[Project]:
        return [self._to_project(meta) for meta in self._store.list_project_meta()]

    def get_project(self, project_id: str) -> Project:
        meta = self._load_meta(project_id)
        return self._to_project(meta)

    def get_status(self, project_id: str) -> ProjectStatus:
        meta = self._load_meta(project_id)
        chapters = self._store.list_chapters(project_id)
        return ProjectStatus(
            project_id=project_id,
            name=meta["name"],
            health=HealthScore(overall=100, session=100, pending_count=0),
            chapter_count=len(chapters),
            onboarding_complete=bool(meta.get("onboarding_complete", False)),
            summary={
                "genre": meta.get("genre"),
                "intervention_level": meta.get("intervention_level"),
                "message": (
                    "引导已完成，可以进入规划与写作。"
                    if meta.get("onboarding_complete")
                    else "项目已初始化，建议先完成创作引导。"
                ),
            },
        )

    def create(self, payload: ProjectCreate) -> Project:
        project_id = uuid4().hex[:12]
        dest = self._store.project_path(project_id)
        if dest.exists():
            raise ProjectAlreadyExistsError(project_id)

        now = datetime.now(UTC).isoformat()
        placeholders = {
            "project_id": project_id,
            "name": payload.name,
            "genre": payload.genre,
            "intervention_level": payload.intervention_level.value,
            "created_at": now,
        }

        self._copy_template(dest, placeholders)

        config_path = dest / "config.yaml"
        config = self._store.read_yaml(config_path)
        config["ollama_model"] = config.get("ollama_model", "qwen2.5:14b")
        self._store.write_yaml(config_path, config)

        meta = self._load_meta(project_id)
        meta["updated_at"] = now
        self._store.write_json(dest / "xsagent.json", meta)
        return self._to_project(meta)

    def update(self, project_id: str, payload: ProjectUpdate) -> Project:
        meta = self._load_meta(project_id)
        if payload.name is not None:
            meta["name"] = payload.name
        if payload.genre is not None:
            meta["genre"] = payload.genre
        if payload.intervention_level is not None:
            meta["intervention_level"] = payload.intervention_level.value
        meta["updated_at"] = datetime.now(UTC).isoformat()
        self._store.write_json(self._store.project_path(project_id) / "xsagent.json", meta)
        return self._to_project(meta)

    def delete(self, project_id: str) -> None:
        self._store.delete_project(project_id)

    def mark_onboarding_complete(self, project_id: str) -> None:
        meta = self._load_meta(project_id)
        meta["onboarding_complete"] = True
        meta["updated_at"] = datetime.now(UTC).isoformat()
        self._store.write_json(self._store.project_path(project_id) / "xsagent.json", meta)

    def _load_meta(self, project_id: str) -> dict:
        if not self._store.exists(project_id):
            raise ProjectNotFoundError(project_id)
        return self._store.read_json(self._store.project_path(project_id) / "xsagent.json")

    def _copy_template(self, dest: Path, placeholders: dict[str, str]) -> None:
        if not self._template_dir.exists():
            raise FileNotFoundError(f"Template not found: {self._template_dir}")

        shutil.copytree(self._template_dir, dest)

        for path in dest.rglob("*"):
            if not path.is_file():
                continue
            if is_macos_metadata(path):
                continue
            if path.suffix in {".json", ".md", ".yaml", ".yml", ".jsonl"} or path.name == ".gitkeep":
                self._substitute_placeholders(path, placeholders)

    def _substitute_placeholders(self, path: Path, placeholders: dict[str, str]) -> None:
        if path.suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            text = json.dumps(data, ensure_ascii=False, indent=2)
            text = _PLACEHOLDER_PATTERN.sub(lambda m: placeholders.get(m.group(1), m.group(0)), text)
            path.write_text(text + "\n", encoding="utf-8")
            return

        if path.suffix in {".yaml", ".yml"}:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            text = yaml.dump(data, allow_unicode=True, default_flow_style=False)
            text = _PLACEHOLDER_PATTERN.sub(lambda m: placeholders.get(m.group(1), m.group(0)), text)
            path.write_text(text, encoding="utf-8")
            return

        if path.suffix in {".md", ".jsonl"} or path.name == ".gitkeep":
            text = path.read_text(encoding="utf-8")
            text = _PLACEHOLDER_PATTERN.sub(lambda m: placeholders.get(m.group(1), m.group(0)), text)
            path.write_text(text, encoding="utf-8")

    def _to_project(self, meta: dict) -> Project:
        project_id = meta["id"]
        return Project(
            id=project_id,
            name=meta["name"],
            genre=meta.get("genre", ""),
            intervention_level=InterventionLevel(meta.get("intervention_level", "balanced")),
            created_at=meta["created_at"],
            updated_at=meta.get("updated_at", meta["created_at"]),
            path=str(self._store.project_path(project_id)),
        )
