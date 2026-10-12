from datetime import UTC, datetime

from xsagent.domain.llm_log.models import LLMLogEntry
from xsagent.storage.project_store import ProjectStore


class LLMLogService:
    def __init__(self, store: ProjectStore) -> None:
        self._store = store

    def append(self, project_id: str, entry: LLMLogEntry) -> LLMLogEntry:
        path = self._store.project_path(project_id) / "logs" / "llm.jsonl"
        self._store.append_jsonl(path, entry.model_dump())
        return entry

    def list_entries(self, project_id: str, limit: int = 50) -> list[LLMLogEntry]:
        path = self._store.project_path(project_id) / "logs" / "llm.jsonl"
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        records = [line for line in lines if line.strip()]
        tail = records[-limit:]
        return [LLMLogEntry.model_validate_json(line) for line in tail]
