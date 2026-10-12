def _wait_job(client, project_id, job_id):
    payload = None
    for _ in range(40):
        job = client.get(f"/api/projects/{project_id}/jobs/{job_id}")
        assert job.status_code == 200
        payload = job.json()
        if payload["status"] in {"completed", "failed"}:
            return payload
    raise AssertionError("job did not finish")


def test_write_volume_job(client, project_id):
    submit = client.post(
        f"/api/projects/{project_id}/jobs/write-volume",
        json={"instruction": "继续写", "limit": 2},
    )
    assert submit.status_code == 202, submit.text
    job = _wait_job(client, project_id, submit.json()["job_id"])
    assert job["status"] == "completed"
    result = job["result"]
    assert result["kind"] == "volume"
    assert len(result["chapters_completed"]) == 2


def test_write_chapter_max_mode(client, project_id):
    submit = client.post(
        f"/api/projects/{project_id}/jobs/write-chapter",
        json={"instruction": "写高潮", "max_mode": True},
    )
    assert submit.status_code == 202
    job = _wait_job(client, project_id, submit.json()["job_id"])
    assert job["status"] == "completed"
    assert job["result"]["max_mode_used"] is True
    assert job["result"]["selected_plan"]


def test_dream_and_distill_endpoints(client, project_id):
    dream = client.post(f"/api/projects/{project_id}/maintenance/dream")
    assert dream.status_code == 200, dream.text
    distill = client.post(f"/api/projects/{project_id}/maintenance/distill")
    assert distill.status_code == 200, distill.text
    assert "added_rules" in distill.json()
