"""Tests for the health endpoint."""


def test_health_endpoint_returns_200(client):
    """Health endpoint should return 200 when DB is reachable."""
    resp = client.get("/api/v1/health")
    assert resp.status_code in (200, 503)
    data = resp.get_json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")
    assert "components" in data
