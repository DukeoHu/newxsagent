import json

import pytest

from xsagent.core.config import get_settings
from xsagent.storage.project_store import ProjectStore


@pytest.fixture
def store(tmp_path):
    return ProjectStore(tmp_path / "data")


def test_read_write_json(store, tmp_path):
    path = tmp_path / "test.json"
    data = {"hello": "世界"}
    store.write_json(path, data)
    assert store.read_json(path) == data


def test_read_write_yaml(store, tmp_path):
    path = tmp_path / "test.yaml"
    data = {"words_per_chapter": 3000}
    store.write_yaml(path, data)
    assert store.read_yaml(path)["words_per_chapter"] == 3000


def test_read_write_md(store, tmp_path):
    path = tmp_path / "ch.md"
    store.write_md(path, "# 标题\n\n正文")
    assert "标题" in store.read_md(path)


def test_list_projects_empty(store):
    assert store.list_project_ids() == []


def test_list_chapters_requires_project(store):
    project_id = "abc"
    project_dir = store.project_path(project_id)
    project_dir.mkdir(parents=True)
    store.write_json(project_dir / "xsagent.json", {"id": project_id, "name": "test"})

    chapters = store.list_chapters(project_id)
    assert chapters == []


def test_append_jsonl(store, tmp_path):
    path = tmp_path / "log.jsonl"
    store.append_jsonl(path, {"a": 1})
    store.append_jsonl(path, {"b": 2})
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert json.loads(lines[0]) == {"a": 1}
    assert json.loads(lines[1]) == {"b": 2}
