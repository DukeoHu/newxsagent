"""LLM 调用日志 API。"""


def test_llm_logs_after_write_chapter(client, project_id):
    submit = client.post(
        f"/api/projects/{project_id}/jobs/write-chapter-sync",
        json={"instruction": "继续写下一章"},
    )
    assert submit.status_code == 200, submit.text

    logs = client.get(f"/api/projects/{project_id}/logs/llm")
    assert logs.status_code == 200
    entries = logs.json()
    assert len(entries) >= 3

    tasks = {entry["task"] for entry in entries}
    assert "prose" in tasks
    assert "bible_sync" in tasks
    assert "drift_detect" in tasks

    prose = next(entry for entry in entries if entry["task"] == "prose")
    assert prose["status"] == "ok"
    assert prose["project_id"] == project_id
    assert prose["prompt"]
    assert prose["response"]
    assert prose["latency_ms"] >= 0


def test_llm_logs_empty_for_new_project(client, project_id):
    resp = client.get(f"/api/projects/{project_id}/logs/llm")
    assert resp.status_code == 200
    assert resp.json() == []
