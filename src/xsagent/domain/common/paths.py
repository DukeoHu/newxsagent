from typing import Any


def _list_index(items: list[Any], part: str) -> int:
    """Resolve list index from numeric part, or by item id/name."""
    if part.isdigit() or (part.startswith("-") and part[1:].isdigit()):
        return int(part)
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        if str(item.get("id", "")) == part or str(item.get("name", "")) == part:
            return idx
    raise KeyError(f"cannot resolve list index: {part!r}")


def get_nested_value(data: Any, path: str) -> Any:
    current = data
    for part in path.split("."):
        if isinstance(current, list):
            current = current[_list_index(current, part)]
        elif isinstance(current, dict):
            current = current[part]
        else:
            raise KeyError(path)
    return current


def set_nested_value(data: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current: Any = data
    for part in parts[:-1]:
        if isinstance(current, list):
            current = current[_list_index(current, part)]
        else:
            if part not in current:
                current[part] = {}
            current = current[part]
    last = parts[-1]
    if isinstance(current, list):
        current[_list_index(current, last)] = value
    else:
        current[last] = value


def append_nested_value(data: dict[str, Any], path: str, value: Any) -> None:
    current = data
    parts = path.split(".")
    for part in parts:
        if isinstance(current, list):
            current = current[_list_index(current, part)]
        else:
            current = current[part]
    if not isinstance(current, list):
        raise TypeError(f"append requires list at path: {path}")
    current.append(value)


def assert_locked_fields_unchanged(
    old_data: dict[str, Any],
    new_data: dict[str, Any],
    locked_fields: list[str],
) -> None:
    from xsagent.core.exceptions import FieldLockedError

    for path in locked_fields:
        try:
            old_value = get_nested_value(old_data, path)
        except (KeyError, IndexError, TypeError, ValueError):
            old_value = None
        try:
            new_value = get_nested_value(new_data, path)
        except (KeyError, IndexError, TypeError, ValueError):
            new_value = None
        if old_value != new_value:
            raise FieldLockedError(path)
