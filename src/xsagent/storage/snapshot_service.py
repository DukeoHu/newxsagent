import shutil
from datetime import UTC, datetime
from pathlib import Path

from xsagent.core.exceptions import ProjectNotFoundError, SnapshotNotFoundError
from xsagent.domain.action_log.models import SnapshotInfo
from xsagent.domain.action_log.service import ActionLogService
from xsagent.storage.project_store import ProjectStore

_SNAPSHOT_DIRS = ("story_bible", "outlines", "chapters", "knowledge")


class SnapshotService:
    def __init__(self, store: ProjectStore, action_log: ActionLogService) -> None:
        self._store = store
        self._action_log = action_log

    def list_snapshots(self, project_id: str) -> list[SnapshotInfo]:
        self._ensure_project(project_id)
        backup_root = self._backup_root(project_id)
        if not backup_root.exists():
            return []
        snapshots: list[SnapshotInfo] = []
        for entry in sorted(backup_root.iterdir(), reverse=True):
            if not entry.is_dir():
                continue
            meta_path = entry / "snapshot.json"
            if meta_path.exists():
                data = self._store.read_json(meta_path)
                snapshots.append(SnapshotInfo.model_validate(data))
            else:
                snapshots.append(
                    SnapshotInfo(
                        id=entry.name,
                        created_at=entry.name,
                        paths=list(_SNAPSHOT_DIRS),
                    )
                )
        return snapshots

    def create(self, project_id: str, label: str | None = None) -> SnapshotInfo:
        self._ensure_project(project_id)
        snapshot_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
        dest = self._backup_root(project_id) / snapshot_id
        dest.mkdir(parents=True, exist_ok=True)
        project_path = self._store.project_path(project_id)

        copied_paths: list[str] = []
        for dirname in _SNAPSHOT_DIRS:
            src = project_path / dirname
            if src.exists():
                shutil.copytree(src, dest / dirname)
                copied_paths.append(dirname)

        info = SnapshotInfo(
            id=snapshot_id,
            created_at=datetime.now(UTC).isoformat(),
            label=label,
            paths=copied_paths,
        )
        self._store.write_json(dest / "snapshot.json", info.model_dump())
        self._action_log.append(
            project_id,
            action_type="snapshot.create",
            diff_summary=f"创建快照 {snapshot_id}",
            metadata={"snapshot_id": snapshot_id, "label": label},
        )
        return info

    def rollback(self, project_id: str, snapshot_id: str) -> SnapshotInfo:
        self._ensure_project(project_id)
        src = self._backup_root(project_id) / snapshot_id
        if not src.is_dir():
            raise SnapshotNotFoundError(snapshot_id)

        pre_rollback = self.create(project_id, label=f"pre-rollback-{snapshot_id}")

        project_path = self._store.project_path(project_id)
        for dirname in _SNAPSHOT_DIRS:
            backup_dir = src / dirname
            target = project_path / dirname
            if backup_dir.exists():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(backup_dir, target)

        self._action_log.append(
            project_id,
            action_type="snapshot.rollback",
            diff_summary=f"回滚至快照 {snapshot_id}",
            rollback_ref=snapshot_id,
            metadata={"pre_rollback_snapshot": pre_rollback.id},
        )

        meta_path = src / "snapshot.json"
        if meta_path.exists():
            return SnapshotInfo.model_validate(self._store.read_json(meta_path))
        return SnapshotInfo(id=snapshot_id, created_at=snapshot_id, paths=list(_SNAPSHOT_DIRS))

    def _backup_root(self, project_id: str) -> Path:
        return self._store.project_path(project_id) / ".backups"

    def _ensure_project(self, project_id: str) -> None:
        if not self._store.exists(project_id):
            raise ProjectNotFoundError(project_id)
