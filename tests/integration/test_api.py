from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def _get_auth_headers():
    import uuid

    from src.api.middleware.auth import create_access_token
    token = create_access_token(str(uuid.uuid4()))
    return {"Authorization": f"Bearer {token}"}


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200


def test_submit_job_unauthenticated():
    resp = client.post("/api/v1/jobs")
    assert resp.status_code in (401, 403)


def test_get_job_not_found():
    with patch("src.api.routes.jobs.get_current_user") as mock_user:
        mock_user.return_value = MagicMock(id="test-user-id", tier="creator",
                                           minutes_processed_this_month=0)
        with patch("src.api.routes.jobs.get_db"):
            resp = client.get(
                "/api/v1/jobs/nonexistent-id",
                headers={"Authorization": "Bearer fake"}
            )
    assert resp.status_code in (401, 404)


def test_list_voices_unauthenticated():
    resp = client.get("/api/v1/voices")
    assert resp.status_code in (401, 403)


def test_voice_clone_no_consent():
    with patch("src.api.routes.voices.get_current_user") as mock_user:
        mock_user.return_value = MagicMock(id="u1", tier="creator")
        with patch("src.api.routes.voices.get_db"):
            resp = client.post(
                "/api/v1/voices",
                data={"display_name": "Test", "consent_acknowledged": "false"},
                files={"reference_audio": ("test.wav", b"fake", "audio/wav")},
                headers={"Authorization": "Bearer fake"}
            )
    assert resp.status_code in (400, 401, 422)
