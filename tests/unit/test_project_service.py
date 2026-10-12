import json
from pathlib import Path

import pytest

from xsagent.core.exceptions import ProjectNotFoundError
from xsagent.domain.project.models import ProjectCreate
from xsagent.domain.project.service import ProjectService
from xsagent.storage.project_store import ProjectStore

REQUIRED_PATHS = [
    "xsagent.json",
    "config.yaml",
    "story_bible/characters.json",
    "story_bible/plot.json",
    "story_bible/world.json",
    "story_bible/notes.json",
    "story_bible/timeline.json",
    "outlines/master.json",
    "chapters/ch_001.md",
    "knowledge/graph.json",
    "logs/actions.jsonl",
]


@pytest.fixture
def service(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    template_dir = repo_root / "templates" / "default"
    store = ProjectStore(tmp_path / "projects")
    return ProjectService(store=store, template_dir=template_dir)


def test_create_project_structure(service):
    project = service.create(ProjectCreate(name="夜半来信", genre="悬疑"))

    for rel in REQUIRED_PATHS:
        assert (Path(project.path) / rel).exists(), f"missing {rel}"

    meta_path = Path(project.path) / "xsagent.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["name"] == "夜半来信"
    assert meta["genre"] == "悬疑"
    assert meta["id"] == project.id


def test_get_status_placeholder_health(service):
    project = service.create(ProjectCreate(name="测试"))
    status = service.get_status(project.id)

    assert status.project_id == project.id
    assert status.health.overall == 100
    assert status.health.pending_count == 0
    assert status.chapter_count == 1
    assert status.onboarding_complete is False


def test_list_projects(service):
    service.create(ProjectCreate(name="A"))
    service.create(ProjectCreate(name="B"))
    names = {p.name for p in service.list_projects()}
    assert names == {"A", "B"}


def test_delete_project(service):
    project = service.create(ProjectCreate(name="待删"))
    project_path = Path(project.path)
    assert project_path.exists()

    service.delete(project.id)

    assert not project_path.exists()
    assert all(p.id != project.id for p in service.list_projects())


def test_delete_project_not_found(service):
    with pytest.raises(ProjectNotFoundError):
        service.delete("nonexistent")
