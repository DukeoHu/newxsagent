import pytest

from xsagent.core.exceptions import FieldLockedError
from xsagent.domain.memory.service import BibleService
from xsagent.domain.project.models import ProjectCreate
from xsagent.domain.project.service import ProjectService
from xsagent.storage.project_store import ProjectStore


@pytest.fixture
def bible_service(tmp_path):
    repo_root = tmp_path.parent.parent.parent  # tests/unit -> tests -> repo? wrong

    # Use actual repo template
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    store = ProjectStore(tmp_path / "data")
    project_service = ProjectService(store=store, template_dir=repo / "templates" / "default")
    project_service.create(ProjectCreate(name="test"))
    pid = store.list_project_ids()[0]
    return BibleService(store), pid


def test_bible_get_put(bible_service):
    service, pid = bible_service
    data = service.get_section(pid, "characters")
    assert data["characters"] == []

    updated = {
        "characters": [{"id": "c1", "name": "林夕", "role": "主角"}],
        "locked_fields": [],
    }
    result = service.put_section(pid, "characters", updated)
    assert result["characters"][0]["name"] == "林夕"


def test_bible_field_lock(bible_service):
    service, pid = bible_service
    service.put_section(
        pid,
        "characters",
        {
            "characters": [{"id": "c1", "name": "林夕"}],
            "locked_fields": ["characters.0.name"],
        },
    )
    with pytest.raises(FieldLockedError):
        service.put_section(
            pid,
            "characters",
            {
                "characters": [{"id": "c1", "name": "改名"}],
                "locked_fields": ["characters.0.name"],
            },
        )
