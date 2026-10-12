from pathlib import Path

from xsagent.domain.outline.service import OutlineService
from xsagent.domain.project.models import ProjectCreate
from xsagent.domain.project.service import ProjectService
from xsagent.storage.project_store import ProjectStore


def test_outline_completion(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    store = ProjectStore(tmp_path / "data")
    ProjectService(store=store, template_dir=repo / "templates" / "default").create(
        ProjectCreate(name="test")
    )
    pid = store.list_project_ids()[0]
    service = OutlineService(store)

    service.put_chapter_blueprint(pid, "ch_001", {"title": "第一章", "status": "completed"})
    service.put_chapter_blueprint(pid, "ch_002", {"title": "第二章", "status": "pending"})

    bundle = service.get_bundle(pid)
    assert bundle.completion == 50.0
    assert len(bundle.chapters) == 2


def test_outline_ignores_macos_appledouble_sidecars(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    store = ProjectStore(tmp_path / "data")
    ProjectService(store=store, template_dir=repo / "templates" / "default").create(
        ProjectCreate(name="test")
    )
    pid = store.list_project_ids()[0]
    service = OutlineService(store)
    chapters = store.project_path(pid) / "outlines" / "chapters"
    sidecar = chapters / "._ch_001.json"
    sidecar.write_bytes(bytes.fromhex("00051607000200004d6163204f532058") + b"\xb0" * 16)

    service.put_master(pid, {"premise": "一份来自旧楼的信"})
    assert service.get_master(pid)["premise"] == "一份来自旧楼的信"
    assert service.list_chapter_blueprints(pid) == []
