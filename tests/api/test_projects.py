def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_project(client):
    create_resp = client.post(
        "/api/projects",
        json={"name": "夜半来信", "genre": "悬疑", "intervention_level": "balanced"},
    )
    assert create_resp.status_code == 201
    project = create_resp.json()
    assert project["name"] == "夜半来信"
    assert project["genre"] == "悬疑"
    assert "id" in project

    get_resp = client.get(f"/api/projects/{project['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "夜半来信"


def test_list_projects(client):
    client.post("/api/projects", json={"name": "项目甲"})
    client.post("/api/projects", json={"name": "项目乙"})

    resp = client.get("/api/projects")
    assert resp.status_code == 200
    names = {p["name"] for p in resp.json()}
    assert names == {"项目甲", "项目乙"}


def test_project_status_m0(client):
    create_resp = client.post("/api/projects", json={"name": "M0 测试"})
    project_id = create_resp.json()["id"]

    status_resp = client.get(f"/api/projects/{project_id}/status")
    assert status_resp.status_code == 200
    status = status_resp.json()
    assert status["project_id"] == project_id
    assert status["health"]["overall"] == 100
    assert status["health"]["pending_count"] == 0
    assert status["chapter_count"] == 1


def test_project_not_found(client):
    resp = client.get("/api/projects/nonexistent/status")
    assert resp.status_code == 404


def test_update_project(client):
    create_resp = client.post("/api/projects", json={"name": "原名"})
    project_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/projects/{project_id}",
        json={"name": "新名", "intervention_level": "aggressive"},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["name"] == "新名"
    assert data["intervention_level"] == "aggressive"


def test_delete_project(client):
    create_resp = client.post("/api/projects", json={"name": "待删项目"})
    project_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/projects/{project_id}")
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/api/projects/{project_id}")
    assert get_resp.status_code == 404

    list_resp = client.get("/api/projects")
    assert list_resp.status_code == 200
    assert all(p["id"] != project_id for p in list_resp.json())


def test_delete_project_not_found(client):
    resp = client.delete("/api/projects/nonexistent")
    assert resp.status_code == 404
