def test_create_explore_and_adopt(client, project_id):
    create_resp = client.post(
        f"/api/projects/{project_id}/explore",
        json={"chapter_id": "ch_001", "prompt": "主角发现新的线索", "count": 3},
    )
    assert create_resp.status_code == 200
    data = create_resp.json()
    assert data["project_id"] == project_id
    assert len(data["options"]) == 3

    option_id = data["options"][0]["option_id"]
    assert data.get("recommended_option_id")
    titles = {item["title"] for item in data["options"]}
    assert len(titles) == 3
    adopt_resp = client.post(
        f"/api/projects/{project_id}/explore/{data['explore_id']}/adopt",
        json={"option_id": option_id, "actor": "tester"},
    )
    assert adopt_resp.status_code == 200
    result = adopt_resp.json()
    assert result["ok"] is True
    assert result["chapter_blueprint"]["chapter_id"] == "ch_001"
    assert result["chapter_blueprint"]["status"] == "ready"
