from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

import pytest
from fastapi.testclient import TestClient

from app.api.files import get_file_storage_service
from app.main import app
from app.services.file_storage import FileStorageService

SAMPLES_DIR = Path(__file__).parent / "samples"


class ClientFactory(Protocol):
    def __call__(
        self,
        max_file_size_bytes: int = 1024,
    ) -> TestClient: ...


@pytest.fixture
def client_factory(tmp_path: Path) -> Iterator[ClientFactory]:
    clients: list[TestClient] = []

    def create_client(max_file_size_bytes: int = 1024) -> TestClient:
        storage_service = FileStorageService(
            storage_dir=tmp_path,
            max_file_size_bytes=max_file_size_bytes,
        )
        app.dependency_overrides[get_file_storage_service] = lambda: storage_service

        client = TestClient(app)
        clients.append(client)
        return client

    yield create_client

    for client in clients:
        client.close()

    app.dependency_overrides.clear()


def test_upload_csv_saves_file_and_returns_metadata(
    client_factory: ClientFactory,
    tmp_path: Path,
) -> None:
    client = client_factory()
    content = (SAMPLES_DIR / "sales.csv").read_bytes()

    response = client.post(
        "/api/files",
        files={
            "file": (
                "sales.csv",
                content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 201

    response_body = response.json()
    file_id = response_body["fileId"]

    assert response_body["fileName"] == "sales.csv"
    assert response_body["sizeBytes"] == len(content)
    assert response_body["uploadedAt"]

    assert (tmp_path / f"{file_id}.csv").read_bytes() == content
    assert (tmp_path / f"{file_id}.json").exists()


def test_upload_rejects_file_with_wrong_extension(
    client_factory: ClientFactory,
    tmp_path: Path,
) -> None:
    client = client_factory()

    response = client.post(
        "/api/files",
        files={
            "file": (
                "notes.txt",
                b"not a csv",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415
    assert response.json() == {"detail": "Only files with the .csv extension are supported."}
    assert list(tmp_path.iterdir()) == []


def test_upload_rejects_file_larger_than_limit(
    client_factory: ClientFactory,
    tmp_path: Path,
) -> None:
    client = client_factory(max_file_size_bytes=10)

    response = client.post(
        "/api/files",
        files={
            "file": (
                "large.csv",
                b"a" * 11,
                "text/csv",
            )
        },
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "The uploaded file exceeds the maximum allowed size."}
    assert list(tmp_path.iterdir()) == []
