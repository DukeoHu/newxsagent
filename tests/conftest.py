import pytest
from fastapi.testclient import TestClient

from xsagent.api.app import create_app
from xsagent.core.config import Settings, reset_settings


@pytest.fixture
def tmp_data_dir(tmp_path):
    return tmp_path / "projects"


@pytest.fixture
def settings(tmp_data_dir, monkeypatch):
    reset_settings()
    monkeypatch.setenv("XSAGENT_DATA_DIR", str(tmp_data_dir))
    monkeypatch.setenv("XSAGENT_LLM_MODE", "simulator")
    reset_settings()
    s = Settings(data_dir=tmp_data_dir)
    return s


@pytest.fixture
def client(settings, monkeypatch):
    reset_settings()
    monkeypatch.setenv("XSAGENT_DATA_DIR", str(settings.data_dir))
    monkeypatch.setenv("XSAGENT_LLM_MODE", "simulator")
    reset_settings()
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def project_id(client):
    resp = client.post("/api/projects", json={"name": "测试项目", "genre": "玄幻"})
    assert resp.status_code == 201
    return resp.json()["id"]
