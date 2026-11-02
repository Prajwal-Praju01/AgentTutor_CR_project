"""Tests for student progress endpoint."""


def test_my_progress_requires_auth(client):
    resp = client.get("/api/v1/students/me/progress")
    assert resp.status_code == 401


def test_my_progress_returns_empty_state(client, auth_headers):
    resp = client.get("/api/v1/students/me/progress", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "concept_scores" in data
    assert "misconceptions" in data
    assert "total_sessions" in data


def test_my_progress_reflects_tutoring_session(client, auth_headers, test_course):
    """After a tutoring session with messages, progress data should update."""
    # Start session and send a message
    sess_resp = client.post("/api/v1/sessions", json={
        "course_id": test_course.id,
        "session_type": "tutoring",
        "concept": "functions",
    }, headers=auth_headers)
    session_id = sess_resp.get_json()["session"]["id"]

    client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"content": "I understand that functions encapsulate reusable code blocks."},
        headers=auth_headers,
    )

    progress_resp = client.get("/api/v1/students/me/progress", headers=auth_headers)
    data = progress_resp.get_json()
    assert data["total_messages"] >= 1

