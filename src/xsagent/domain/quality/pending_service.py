from xsagent.domain.quality.models import PendingItem, PendingItemStatus
from xsagent.storage.project_store import ProjectStore


class PendingService:
    def __init__(self, store: ProjectStore) -> None:
        self._store = store

    def _path(self, project_id: str):
        return self._store.project_path(project_id) / "logs" / "pending.json"

    def list_pending(self, project_id: str) -> list[PendingItem]:
        path = self._path(project_id)
        if not path.exists():
            return []
        data = self._store.read_json(path)
        items = [PendingItem.model_validate(item) for item in data.get("items", [])]
        return [i for i in items if i.status == PendingItemStatus.PENDING]

    def list_all(self, project_id: str) -> list[PendingItem]:
        path = self._path(project_id)
        if not path.exists():
            return []
        data = self._store.read_json(path)
        return [PendingItem.model_validate(item) for item in data.get("items", [])]

    def add(self, item: PendingItem) -> PendingItem:
        path = self._path(project_id := item.project_id)
        data = {"items": []}
        if path.exists():
            data = self._store.read_json(path)
        data.setdefault("items", []).append(item.model_dump())
        self._store.write_json(path, data)
        return item

    def resolve(self, project_id: str, item_id: str, status: PendingItemStatus) -> PendingItem:
        path = self._path(project_id)
        data = self._store.read_json(path)
        for raw in data.get("items", []):
            if raw["id"] == item_id:
                raw["status"] = status.value
                self._store.write_json(path, data)
                return PendingItem.model_validate(raw)
        raise KeyError(item_id)

    def count_pending(self, project_id: str) -> int:
        return len(self.list_pending(project_id))
