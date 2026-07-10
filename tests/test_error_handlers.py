from fastapi.testclient import TestClient

from app.main import app


def test_unknown_route_returns_unified_error() -> None:
    with TestClient(app) as client:
        response = client.get("/unknown-route")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Not Found",
            "details": None,
        }
    }


def test_invalid_file_id_returns_validation_error() -> None:
    with TestClient(app) as client:
        response = client.get("/api/files/not-a-valid-uuid")

    assert response.status_code == 422

    body = response.json()

    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "Request validation failed."
    assert body["error"]["details"]
    assert body["error"]["details"][0]["field"] == "path.file_id"
