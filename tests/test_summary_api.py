import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestSummaryAPI:
    """Fast, non-heavy tests for AI summary endpoints (no model calls)."""

    def test_get_summary_not_found(self):
        # When summary has not been generated, API should return found False
        res = client.get("/api/summary/get", params={"video_path": "nonexistent/course/vid.mp4"})
        assert res.status_code == 200
        data = res.json()
        assert data.get("found") is False

    def test_start_summary_missing_video(self):
        # Starting a summary for a non-existent video returns 404
        res = client.post("/api/summary/start", json={"video_path": "nonexistent/course/vid.mp4", "force": True})
        assert res.status_code == 404

    def test_summary_status_unknown_task(self):
        # Unknown task id returns 404
        res = client.get("/api/summary/status/00000000-0000-0000-0000-000000000000")
        assert res.status_code == 404


def test_versions_endpoint_empty(test_client: TestClient):
    r = test_client.get("/api/summary/versions", params={"video_path": "does/not/exist.mp4"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["versions"], list)


def test_versions_and_specific_version_with_fake_ai(test_client: TestClient, fake_ai):
    # Start a summary (fake AI completes immediately)
    start = test_client.post("/api/summary/start", json={"video_path": "/tmp/videoA.mp4", "force": True})
    assert start.status_code == 200
    g = test_client.get("/api/summary/get", params={"video_path": "/tmp/videoA.mp4"})
    assert g.status_code == 200
    assert g.json().get("found") is True
    v = test_client.get("/api/summary/versions", params={"video_path": "/tmp/videoA.mp4"})
    assert v.status_code == 200
    versions = v.json()["versions"]
    assert isinstance(versions, list)
    if versions:
        ver = versions[0]["version"]
        sv = test_client.get("/api/summary/version", params={"video_path": "/tmp/videoA.mp4", "version": ver})
        assert sv.status_code == 200
        assert "summary" in sv.json()

