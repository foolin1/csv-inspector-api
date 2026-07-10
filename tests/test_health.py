from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_application_information() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "CSV Inspector API",
        "version": "0.2.0",
        "docs": "/docs",
    }


def test_health_check_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
