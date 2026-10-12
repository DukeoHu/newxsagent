"""P2 里程碑 M2：API 触发写作闭环。"""


def test_m2_write_chapter_flow(client, project_id):
    submit = client.post(
        f"/api/projects/{project_id}/jobs/write-chapter",
        json={"instruction": "继续写下一章"},
    )
    assert submit.status_code == 202, submit.text
    job_id = submit.json()["job_id"]
    data = None
    for _ in range(30):
        job = client.get(f"/api/projects/{project_id}/jobs/{job_id}")
        assert job.status_code == 200
        payload = job.json()
        if payload["status"] in {"completed", "failed"}:
            data = payload["result"]
            break
    assert data is not None
    assert data["status"] == "completed"
    assert data["word_count"] > 0
    assert data["sync_patch"] is not None
    assert data["sync_apply"] is not None
    assert data["drift_findings_count"] >= 1
    assert len(data["pending_ids"]) >= 1

    chars = client.get(f"/api/projects/{project_id}/bible/characters").json()
    assert len(chars["characters"]) >= 1

    pending = client.get(f"/api/projects/{project_id}/pending").json()
    assert len(pending) >= 1
    assert any(p["risk_level"] == "high" for p in pending)

    logs = client.get(f"/api/projects/{project_id}/logs/actions").json()
    types = {log["action_type"] for log in logs}
    assert "write.chapter" in types
    assert "bible_sync.apply" in types


def test_bible_patch_preview(client, project_id):
    patch_body = {
        "patch": {
            "updates": [
                {
                    "section": "notes",
                    "op": "set",
                    "path": "style_notes",
                    "value": "冷峻写实",
                }
            ],
            "risk_level": "low",
            "explanation": "设置风格",
        },
        "apply": True,
    }
    resp = client.post(f"/api/projects/{project_id}/bible/patch", json=patch_body)
    assert resp.status_code == 200
    notes = client.get(f"/api/projects/{project_id}/bible/notes").json()
    assert notes["style_notes"] == "冷峻写实"
