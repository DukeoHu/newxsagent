import yaml


def test_get_llm_settings(client):
    resp = client.get("/api/settings/llm")
    assert resp.status_code == 200
    data = resp.json()
    assert "mode" in data
    assert "ollama_model" in data
    assert "deepseek_model" in data


def test_update_llm_settings(client, tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    monkeypatch.setenv("XSAGENT_CONFIG_PATH", str(config_path))
    monkeypatch.delenv("XSAGENT_LLM_MODE", raising=False)

    put_resp = client.put(
        "/api/settings/llm",
        json={
            "mode": "deepseek",
            "ollama_base_url": "http://127.0.0.1:11434",
            "ollama_model": "qwen2.5:14b",
            "ollama_think": False,
            "strip_think_tags": True,
            "deepseek_base_url": "https://api.deepseek.com",
            "deepseek_api_key": "test_key_123",
            "deepseek_model": "deepseek-v4-pro",
            "deepseek_reasoning_effort": "high",
            "deepseek_thinking_enabled": True,
        },
    )
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert data["mode"] == "deepseek"
    assert data["deepseek_model"] == "deepseek-v4-pro"
    assert data["deepseek_api_key"] == "test_key_123"

    assert config_path.exists()
    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert saved["llm"]["deepseek_model"] == "deepseek-v4-pro"
