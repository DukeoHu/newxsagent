from datetime import UTC, datetime

from xsagent.domain.action_log.models import ActionLogEntry
from xsagent.storage.project_store import ProjectStore


class ActionLogService:
    def __init__(self, store: ProjectStore) -> None:
        self._store = store

    def append(
        self,
        project_id: str,
        action_type: str,
        diff_summary: str = "",
        rollback_ref: str | None = None,
        metadata: dict | None = None,
    ) -> ActionLogEntry:
        entry = ActionLogEntry(
            timestamp=datetime.now(UTC).isoformat(),
            action_type=action_type,
            diff_summary=diff_summary,
            rollback_ref=rollback_ref,
            metadata=metadata or {},
        )
        path = self._store.project_path(project_id) / "logs" / "actions.jsonl"
        self._store.append_jsonl(path, entry.model_dump())
        return entry

    def list_entries(self, project_id: str, limit: int = 50) -> list[ActionLogEntry]:
        path = self._store.project_path(project_id) / "logs" / "actions.jsonl"
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        records = [line for line in lines if line.strip()]
        tail = records[-limit:]
        return [ActionLogEntry.model_validate_json(line) for line in tail]
