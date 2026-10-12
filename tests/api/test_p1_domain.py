"""P1 里程碑 M1：Bible + 章节 API + 快照回滚。"""


def test_m1_bible_chapter_snapshot_flow(client, project_id):
    # Bible CRUD
    chars = client.get(f"/api/projects/{project_id}/bible/characters").json()
    assert chars["characters"] == []

    put_resp = client.put(
        f"/api/projects/{project_id}/bible/characters",
        json={
            "data": {
                "characters": [{"id": "c1", "name": "林夕", "role": "主角"}],
                "locked_fields": ["characters.0.name"],
            }
        },
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["characters"][0]["name"] == "林夕"

    locked_resp = client.put(
        f"/api/projects/{project_id}/bible/characters",
        json={
            "data": {
                "characters": [{"id": "c1", "name": "改名"}],
                "locked_fields": ["characters.0.name"],
            }
        },
    )
    assert locked_resp.status_code == 409

    # Chapter CRUD
    list_resp = client.get(f"/api/projects/{project_id}/chapters")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    create_resp = client.post(
        f"/api/projects/{project_id}/chapters",
        json={"id": "ch_002", "title": "第二章", "content_md": "# 第二章\n\n正文。"},
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["word_count"] > 0

    delete_resp = client.delete(f"/api/projects/{project_id}/chapters/ch_002")
    assert delete_resp.status_code == 204
    assert len(client.get(f"/api/projects/{project_id}/chapters").json()) == 1

    # Outline
    outline_resp = client.get(f"/api/projects/{project_id}/outlines")
    assert outline_resp.status_code == 200

    client.put(
        f"/api/projects/{project_id}/outlines/chapters/ch_001",
        json={"title": "第一章", "status": "completed"},
    )
    master = client.get(f"/api/projects/{project_id}/outlines/master").json()
    assert master["completion"] > 0

    # Snapshot before mutation
    snap_resp = client.post(f"/api/projects/{project_id}/snapshots", json={"label": "m1"})
    assert snap_resp.status_code == 201
    snapshot_id = snap_resp.json()["id"]

    client.put(
        f"/api/projects/{project_id}/bible/characters",
        json={
            "data": {
                "characters": [{"id": "c1", "name": "林夕", "role": "反派"}],
                "locked_fields": ["characters.0.name"],
            }
        },
    )

    rollback_resp = client.post(f"/api/projects/{project_id}/snapshots/{snapshot_id}/rollback")
    assert rollback_resp.status_code == 200

    restored = client.get(f"/api/projects/{project_id}/bible/characters").json()
    assert restored["characters"][0]["role"] == "主角"

    logs = client.get(f"/api/projects/{project_id}/logs/actions").json()
    assert any(log["action_type"] == "snapshot.rollback" for log in logs)
