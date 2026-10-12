import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from xsagent.core.exceptions import ProjectNotFoundError


def is_macos_metadata(path: Path) -> bool:
    """AppleDouble sidecars (``._*``) and Finder metadata copied from macOS."""
    name = path.name
    return name.startswith("._") or name == ".DS_Store"


class ProjectStore:
    """File-system backed storage for project data."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    def project_path(self, project_id: str) -> Path:
        return self._data_dir / project_id

    def exists(self, project_id: str) -> bool:
        meta = self.project_path(project_id) / "xsagent.json"
        return meta.is_file()

    def delete_project(self, project_id: str) -> None:
        if not self.exists(project_id):
            raise ProjectNotFoundError(project_id)
        shutil.rmtree(self.project_path(project_id))

    def list_project_ids(self) -> list[str]:
        ids: list[str] = []
        if not self._data_dir.exists():
            return ids
        for entry in sorted(self._data_dir.iterdir()):
            if entry.is_dir() and (entry / "xsagent.json").is_file():
                ids.append(entry.name)
        return ids

    def list_project_meta(self) -> list[dict[str, Any]]:
        return [self.read_json(self.project_path(pid) / "xsagent.json") for pid in self.list_project_ids()]

    def read_json(self, path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    def read_yaml(self, path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def write_yaml(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def read_md(self, path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(str(path))
        return path.read_text(encoding="utf-8")

    def write_md(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def list_chapters(self, project_id: str) -> list[str]:
        if not self.exists(project_id):
            raise ProjectNotFoundError(project_id)
        chapters_dir = self.project_path(project_id) / "chapters"
        if not chapters_dir.exists():
            return []
        return sorted(
            p.name for p in chapters_dir.glob("*.md") if not is_macos_metadata(p)
        )

    def append_jsonl(self, path: Path, record: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
