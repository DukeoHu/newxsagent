"""真·蓝图生成 API：总纲 + 章节 beats。"""


def _seed_scale(client, project_id):
    for i in range(1, 4):
        cid = f"ch_{i:03d}"
        client.put(
            f"/api/projects/{project_id}/outlines/chapters/{cid}",
            json={
                "chapter_id": cid,
                "title": f"第{i}章",
                "beats": [],
                "constraints": [],
                "status": "pending",
            },
        )
    client.put(
        f"/api/projects/{project_id}/outlines/volumes/vol_01",
        json={"title": "第1卷", "arcs": [], "chapter_range": [1, 3]},
    )


def test_generate_master_outline(client, project_id):
    _seed_scale(client, project_id)
    client.put(
        f"/api/projects/{project_id}/bible/characters",
        json={
            "data": {
                "characters": [{"id": "c1", "name": "林夕", "role": "主角"}],
                "locked_fields": [],
            }
        },
    )

    resp = client.post(f"/api/projects/{project_id}/outlines/generate-master")
    assert resp.status_code == 200
    data = resp.json()
    assert data["master"]["acts"]
    assert data["master"]["ending_goal"]

    master = client.get(f"/api/projects/{project_id}/outlines/master").json()
    assert master["ending_goal"]
    assert master["acts"]


def test_generate_chapter_blueprint(client, project_id):
    _seed_scale(client, project_id)
    client.post(f"/api/projects/{project_id}/outlines/generate-master")

    preview = client.post(
        f"/api/projects/{project_id}/outlines/chapters/ch_001/generate",
    )
    assert preview.status_code == 200
    rec = preview.json()
    assert rec["chapter_id"] == "ch_001"
    assert len(rec["beats"]) >= 3

    apply = client.post(
        f"/api/projects/{project_id}/outlines/generate",
        json={"scope": "chapters", "chapter_ids": ["ch_001"], "apply": True},
    )
    assert apply.status_code == 200
    stored = client.get(f"/api/projects/{project_id}/outlines/chapters/ch_001").json()
    assert stored["beats"]
    assert stored["status"] == "ready"


def test_generate_volume_pending_only(client, project_id):
    _seed_scale(client, project_id)
    client.put(
        f"/api/projects/{project_id}/outlines/master",
        json={
            "acts": [{"id": "act_1", "title": "测试", "summary": "测试", "chapter_range": [1, 3]}],
            "themes": ["测试"],
            "ending_goal": "测试终局",
        },
    )

    client.put(
        f"/api/projects/{project_id}/outlines/chapters/ch_001",
        json={
            "chapter_id": "ch_001",
            "title": "第一章",
            "beats": ["已有节拍"],
            "constraints": [],
            "status": "ready",
        },
    )

    resp = client.post(
        f"/api/projects/{project_id}/outlines/generate",
        json={"scope": "volume", "volume_id": "vol_01", "only_pending": True},
    )
    assert resp.status_code == 200
    assert resp.json()["applied"] == 2

    ch2 = client.get(f"/api/projects/{project_id}/outlines/chapters/ch_002").json()
    assert ch2["beats"]
    ch1 = client.get(f"/api/projects/{project_id}/outlines/chapters/ch_001").json()
    assert ch1["beats"] == ["已有节拍"]
