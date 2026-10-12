"""创作引导 API：深度问答 → 生成草案 → 应用。"""

from xsagent.domain.onboarding.service import ONBOARDING_OPENING_QUESTION


def test_onboarding_qa_flow(client, project_id):
    status = client.get(f"/api/projects/{project_id}/status").json()
    assert status["onboarding_complete"] is False

    start = client.post(f"/api/projects/{project_id}/onboarding/start")
    assert start.status_code == 200
    data = start.json()
    assert data["question"] == ONBOARDING_OPENING_QUESTION
    assert data["session"]["turns"][0]["content"] == ONBOARDING_OPENING_QUESTION
    assert data["session"]["turns"][0]["question_id"] == "q_opening"
    assert data["session"]["status"] == "active"

    for answer in [
        "一个少年在废弃邮局收到神秘来信，卷入隐藏世界。",
        "主角林夕，冷静敏锐，想查明身世并保护妹妹。",
        "现代都市下有古物共鸣的隐秘规则，旧邮局是入口。",
    ]:
        resp = client.post(
            f"/api/projects/{project_id}/onboarding/answer",
            json={"answer": answer},
        )
        assert resp.status_code == 200

    ready = resp.json()
    assert ready["ready_to_generate"] is True

    draft_resp = client.post(f"/api/projects/{project_id}/onboarding")
    assert draft_resp.status_code == 200
    payload = draft_resp.json()
    draft = payload["draft"]
    assert payload["llm_mode"] == "simulator"
    assert payload["warning"]
    assert draft["characters"]["characters"]
    assert draft["plot"]["themes"]
    assert draft["notes"]["style_rules"]
    assert len(draft["notes"]["style_rules"]) >= 3
    assert draft["notes"]["style_rules"][0]["category"]
    assert draft["notes"]["style_rules"][0]["priority"] in {"must", "should", "prefer"}

    session_after_draft = client.get(f"/api/projects/{project_id}/onboarding/session")
    assert session_after_draft.status_code == 200
    persisted = session_after_draft.json()
    assert persisted["draft"]["characters"]["characters"]
    assert persisted["status"] == "ready"

    apply_resp = client.post(
        f"/api/projects/{project_id}/onboarding/apply",
        json={"bible": draft},
    )
    assert apply_resp.status_code == 200

    status = client.get(f"/api/projects/{project_id}/status").json()
    assert status["onboarding_complete"] is True

    chars = client.get(f"/api/projects/{project_id}/bible/characters").json()
    assert len(chars["characters"]) >= 1
    notes = client.get(f"/api/projects/{project_id}/bible/notes").json()
    assert "引导问答提炼" in notes["author_notes"]
    assert "废弃邮局" in notes["author_notes"]
    assert notes["style_rules"]
    assert notes["style_rules"][0]["title"]
    assert notes["style_notes"]


def test_onboarding_generate_without_session(client, project_id):
    resp = client.post(f"/api/projects/{project_id}/onboarding")
    assert resp.status_code == 400


def _ready_with_draft(client, project_id):
    client.post(f"/api/projects/{project_id}/onboarding/start")
    for answer in [
        "一个少年在废弃邮局收到神秘来信，卷入隐藏世界。",
        "主角林夕，冷静敏锐，想查明身世并保护妹妹。",
        "现代都市下有古物共鸣的隐秘规则，旧邮局是入口。",
    ]:
        client.post(
            f"/api/projects/{project_id}/onboarding/answer",
            json={"answer": answer},
        )
    draft_resp = client.post(f"/api/projects/{project_id}/onboarding")
    assert draft_resp.status_code == 200
    return draft_resp.json()["draft"]


def test_onboarding_clear_draft_keeps_turns(client, project_id):
    draft = _ready_with_draft(client, project_id)
    assert draft["characters"]["characters"]

    cleared = client.post(f"/api/projects/{project_id}/onboarding/clear-draft")
    assert cleared.status_code == 200
    session = cleared.json()
    assert session["draft"] is None
    assert session["status"] == "ready"
    assert any(t["role"] == "user" for t in session["turns"])

    persisted = client.get(f"/api/projects/{project_id}/onboarding/session").json()
    assert persisted["draft"] is None
    assert len(persisted["turns"]) >= 4


def test_onboarding_partial_apply(client, project_id):
    draft = _ready_with_draft(client, project_id)
    partial = {"characters": draft["characters"]}

    apply_resp = client.post(
        f"/api/projects/{project_id}/onboarding/apply",
        json={"bible": partial},
    )
    assert apply_resp.status_code == 200

    chars = client.get(f"/api/projects/{project_id}/bible/characters").json()
    assert len(chars["characters"]) >= 1

    notes = client.get(f"/api/projects/{project_id}/bible/notes").json()
    assert "引导问答提炼" not in (notes.get("author_notes") or "")


def test_onboarding_apply_requires_sections(client, project_id):
    client.post(f"/api/projects/{project_id}/onboarding/start")
    client.post(
        f"/api/projects/{project_id}/onboarding/answer",
        json={"answer": "先给一个短故事设定。"},
    )
    resp = client.post(
        f"/api/projects/{project_id}/onboarding/apply",
        json={"bible": {}},
    )
    assert resp.status_code == 400
