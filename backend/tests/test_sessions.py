"""Tests for sessions and the tutoring orchestrator."""


def test_create_tutoring_session(client, auth_headers, test_course):
    resp = client.post("/api/v1/sessions", json={
        "course_id": test_course.id,
        "session_type": "tutoring",
        "title": "Test Tutoring Session",
        "concept": "recursion",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["session"]["session_type"] == "tutoring"
    assert data["session"]["status"] == "active"


def test_create_debugging_session(client, auth_headers, test_course):
    resp = client.post("/api/v1/sessions", json={
        "session_type": "debugging",
        "title": "Fix the Bug",
        "description": "The function returns wrong value",
        "buggy_code": "def add(a, b):\n    return a - b",
        "language": "python",
        "expected_behavior": "Should return a + b",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["session"]["session_type"] == "debugging"


def test_debugging_session_requires_code(client, auth_headers):
    resp = client.post("/api/v1/sessions", json={
        "session_type": "debugging",
        "title": "No code provided",
    }, headers=auth_headers)
    assert resp.status_code == 422


def test_send_message_to_tutoring_session(client, auth_headers, test_course):
    # Create session
    sess_resp = client.post("/api/v1/sessions", json={
        "course_id": test_course.id,
        "session_type": "tutoring",
        "concept": "loops",
    }, headers=auth_headers)
    session_id = sess_resp.get_json()["session"]["id"]

    # Send message
    msg_resp = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"content": "I don't understand how for loops work."},
        headers=auth_headers,
    )
    assert msg_resp.status_code == 200
    data = msg_resp.get_json()
    assert "student_message" in data
    assert "tutor_message" in data
    assert data["tutor_message"]["role"] == "tutor"
    assert len(data["tutor_message"]["content"]) > 0


def test_get_session_history(client, auth_headers, test_course):
    # Create and send a message
    sess_resp = client.post("/api/v1/sessions", json={
        "course_id": test_course.id,
        "session_type": "tutoring",
    }, headers=auth_headers)
    session_id = sess_resp.get_json()["session"]["id"]

    client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"content": "What is a variable?"},
        headers=auth_headers,
    )

    hist_resp = client.get(f"/api/v1/sessions/{session_id}/history", headers=auth_headers)
    assert hist_resp.status_code == 200
    data = hist_resp.get_json()
    assert len(data["messages"]) == 2  # student + tutor


def test_cannot_access_other_users_session(client, db_session, auth_headers):
    """Cross-user session access should be denied."""
    import bcrypt
    from app.models import User, UserRole, Session, SessionType, SessionStatus, StudentModel

    # Create another user and their session
    pw_hash = bcrypt.hashpw(b"OtherPass123!", bcrypt.gensalt()).decode()
    other_user = User(
        email="other@test.com",
        username="otheruser",
        password_hash=pw_hash,
        role=UserRole.student,
    )
    db_session.add(other_user)
    db_session.flush()

    sm = StudentModel(user_id=other_user.id)
    db_session.add(sm)

    other_session = Session(
        student_id=other_user.id,
        session_type=SessionType.tutoring,
        status=SessionStatus.active,
    )
    db_session.add(other_session)
    db_session.flush()

    resp = client.get(
        f"/api/v1/sessions/{other_session.id}",
        headers=auth_headers,
    )
    assert resp.status_code == 403
