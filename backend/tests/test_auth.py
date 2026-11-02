"""Tests for auth endpoints."""


def test_register_new_user(client, db_session):
    resp = client.post("/api/v1/auth/register", json={
        "email": "new@test.com",
        "username": "newuser",
        "password": "SecurePass123!",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "new@test.com"


def test_register_duplicate_email_rejected(client, test_user):
    resp = client.post("/api/v1/auth/register", json={
        "email": test_user.email,
        "username": "differentuser",
        "password": "SecurePass123!",
    })
    assert resp.status_code == 422


def test_login_valid_credentials(client, test_user):
    resp = client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "TestPass123!",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert "access_token" in data


def test_login_invalid_password_rejected(client, test_user):
    resp = client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "WrongPassword!",
    })
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_returns_user(client, test_user, auth_headers):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["user"]["email"] == test_user.email
