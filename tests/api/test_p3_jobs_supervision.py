def test_submit_job_and_query_status(client, project_id):
    submit = client.post(
        f"/api/projects/{project_id}/jobs/write-chapter-submit",
        json={"instruction": "继续写下一章"},
    )
    assert submit.status_code == 202
    job_id = submit.json()["job_id"]

    # simple poll in testclient
    for _ in range(20):
        job = client.get(f"/api/projects/{project_id}/jobs/{job_id}")
        assert job.status_code == 200
        if job.json()["status"] in {"completed", "failed"}:
            break
    assert job.json()["status"] == "completed"


def test_supervision_and_resolve(client, project_id):
    submit = client.post(f"/api/projects/{project_id}/jobs/write-chapter", json={"instruction": "继续写"})
    assert submit.status_code == 202
    job_id = submit.json()["job_id"]
    for _ in range(20):
        state = client.get(f"/api/projects/{project_id}/jobs/{job_id}").json()
        if state["status"] in {"completed", "failed"}:
            break

    supervision = client.get(f"/api/projects/{project_id}/supervision")
    assert supervision.status_code == 200
    data = supervision.json()
    assert "health" in data and "pending_items" in data

    pending = data["pending_items"]
    if pending:
        item_id = pending[0]["id"]
        resolved = client.post(
            f"/api/projects/{project_id}/supervision/resolve",
            json={"pending_id": item_id, "action": "rollback", "actor": "test"},
        )
        assert resolved.status_code == 200
        assert resolved.json()["ok"] is True


def test_job_events_sse(client, project_id):
    submit = client.post(
        f"/api/projects/{project_id}/jobs/write-chapter-submit",
        json={"instruction": "继续写下一章"},
    )
    job_id = submit.json()["job_id"]

    with client.stream("GET", f"/api/projects/{project_id}/jobs/{job_id}/events") as resp:
        assert resp.status_code == 200
        body = "".join(resp.iter_text())
    assert "event: job.progress" in body
    assert "event: job.chunk" in body


def test_job_events_sse_resume_with_last_event_id(client, project_id):
    submit = client.post(
        f"/api/projects/{project_id}/jobs/write-chapter-submit",
        json={"instruction": "继续写下一章"},
    )
    job_id = submit.json()["job_id"]

    with client.stream(
        "GET",
        f"/api/projects/{project_id}/jobs/{job_id}/events",
        headers={"Last-Event-ID": "0"},
    ) as resp:
        assert resp.status_code == 200
        body = "".join(resp.iter_text())
    assert "id: 0" not in body
    assert "event: job.progress" in body
