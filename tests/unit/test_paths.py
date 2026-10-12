import pytest

from xsagent.core.exceptions import FieldLockedError
from xsagent.domain.common.paths import (
    assert_locked_fields_unchanged,
    get_nested_value,
    set_nested_value,
)


def test_get_nested_value():
    data = {"characters": [{"name": "林夕"}]}
    assert get_nested_value(data, "characters.0.name") == "林夕"


def test_get_nested_value_by_name_or_id():
    data = {
        "characters": [
            {"id": "char_lin_yuan", "name": "林渊", "current_state": "刚重生"},
            {"id": "char_su", "name": "苏清禾", "current_state": "年级第一"},
        ]
    }
    assert get_nested_value(data, "characters.林渊.current_state") == "刚重生"
    assert get_nested_value(data, "characters.char_su.current_state") == "年级第一"


def test_set_nested_value_by_name():
    data = {
        "characters": [
            {"id": "char_lin_yuan", "name": "林渊", "current_state": "刚重生"},
        ]
    }
    set_nested_value(data, "characters.林渊.current_state", "体能仍差，但已起床")
    assert data["characters"][0]["current_state"] == "体能仍差，但已起床"


def test_locked_field_blocks_change():
    old = {"characters": [{"name": "林夕"}], "locked_fields": ["characters.0.name"]}
    new = {"characters": [{"name": "林夜"}], "locked_fields": ["characters.0.name"]}
    with pytest.raises(FieldLockedError):
        assert_locked_fields_unchanged(old, new, old["locked_fields"])


def test_locked_field_allows_unchanged():
    old = {"characters": [{"name": "林夕"}], "locked_fields": ["characters.0.name"]}
    new = {"characters": [{"name": "林夕", "role": "主角"}], "locked_fields": ["characters.0.name"]}
    assert_locked_fields_unchanged(old, new, old["locked_fields"])
