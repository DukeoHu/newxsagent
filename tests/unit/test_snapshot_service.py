from pathlib import Path

from xsagent.domain.action_log.service import ActionLogService
from xsagent.domain.memory.service import BibleService
from xsagent.domain.project.models import ProjectCreate
from xsagent.domain.project.service import ProjectService
from xsagent.storage.project_store import ProjectStore
from xsagent.storage.snapshot_service import SnapshotService


def test_snapshot_rollback_restores_bible(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    store = ProjectStore(tmp_path / "data")
    ProjectService(store=store, template_dir=repo / "templates" / "default").create(
        ProjectCreate(name="test")
    )
    pid = store.list_project_ids()[0]

    bible = BibleService(store)
    action_log = ActionLogService(store)
    snapshots = SnapshotService(store, action_log)

    original = bible.get_section(pid, "characters")
    snapshot = snapshots.create(pid, label="before-edit")

    bible.put_section(
        pid,
        "characters",
        {"characters": [{"id": "c1", "name": "修改后"}], "locked_fields": []},
    )
    assert bible.get_section(pid, "characters")["characters"][0]["name"] == "修改后"

    snapshots.rollback(pid, snapshot.id)
    restored = bible.get_section(pid, "characters")
    assert restored == original

    logs = action_log.list_entries(pid)
    action_types = [e.action_type for e in logs]
    assert "snapshot.create" in action_types
    assert "snapshot.rollback" in action_types
