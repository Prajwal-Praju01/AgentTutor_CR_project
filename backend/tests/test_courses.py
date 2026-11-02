"""Tests for courses endpoints."""


def test_create_course(client, auth_headers):
    resp = client.post("/api/v1/courses", json={
        "title": "New Test Course",
        "code": "NTC101",
        "description": "A new course for testing",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["course"]["code"] == "NTC101"
    assert data["course"]["title"] == "New Test Course"


def test_create_course_duplicate_code_rejected(client, auth_headers, test_course):
    resp = client.post("/api/v1/courses", json={
        "title": "Duplicate Code Course",
        "code": test_course.code,
    }, headers=auth_headers)
    assert resp.status_code == 422


def test_list_courses_requires_auth(client):
    resp = client.get("/api/v1/courses")
    assert resp.status_code == 401


def test_list_courses(client, auth_headers, test_course):
    resp = client.get("/api/v1/courses", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "courses" in data
    assert any(c["id"] == test_course.id for c in data["courses"])


def test_get_course(client, auth_headers, test_course):
    resp = client.get(f"/api/v1/courses/{test_course.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["course"]["id"] == test_course.id


def test_get_nonexistent_course_returns_404(client, auth_headers):
    resp = client.get("/api/v1/courses/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404
