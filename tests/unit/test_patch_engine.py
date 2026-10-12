import pytest

from xsagent.domain.memory.patch_models import BiblePatch, PatchUpdate, RiskLevel
from xsagent.domain.memory.patch_engine import PatchEngine
from xsagent.domain.memory.service import BibleService
from xsagent.domain.project.models import ProjectCreate
from xsagent.domain.project.service import ProjectService
from xsagent.storage.project_store import ProjectStore


@pytest.fixture
def patch_engine(tmp_path):
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    store = ProjectStore(tmp_path / "data")
    ProjectService(store=store, template_dir=repo / "templates" / "default").create(
        ProjectCreate(name="test")
    )
    pid = store.list_project_ids()[0]
    bible = BibleService(store)
    return PatchEngine(bible), pid, bible


def test_patch_preview_and_apply(patch_engine):
    engine, pid, bible = patch_engine
    patch = BiblePatch(
        updates=[
            PatchUpdate(
                section="characters",
                op="append",
                path="characters",
                value={"id": "c1", "name": "林夕"},
            )
        ],
        risk_level=RiskLevel.LOW,
        explanation="test",
    )
    previews = engine.preview(pid, patch)
    assert previews[0].after["characters"]

    engine.apply(pid, patch)
    data = bible.get_section(pid, "characters")
    assert len(data["characters"]) == 1


def test_patch_set_by_character_name(patch_engine):
    engine, pid, bible = patch_engine
    bible.put_section(
        pid,
        "characters",
        {
            "characters": [
                {"id": "char_lin_yuan", "name": "林渊", "current_state": "刚重生"},
            ],
            "locked_fields": [],
        },
    )
    patch = BiblePatch(
        updates=[
            PatchUpdate(
                section="characters",
                op="set",
                path="characters.林渊.current_state",
                value="已适应课堂",
            )
        ],
        risk_level=RiskLevel.LOW,
        explanation="sync by name",
    )
    engine.apply(pid, patch)
    data = bible.get_section(pid, "characters")
    assert data["characters"][0]["current_state"] == "已适应课堂"


def test_patch_respects_lock(patch_engine):
    engine, pid, bible = patch_engine
    bible.put_section(
        pid,
        "characters",
        {"characters": [{"id": "c1", "name": "林夕"}], "locked_fields": ["characters.0.name"]},
    )
    patch = BiblePatch(
        updates=[
            PatchUpdate(section="characters", op="set", path="characters.0.name", value="改名")
        ],
        risk_level=RiskLevel.LOW,
    )
    with pytest.raises(Exception):
        engine.apply(pid, patch)
