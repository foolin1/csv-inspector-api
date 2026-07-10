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
    assert response_body["encoding"] == "UTF-8"
    assert response_body["delimiter"] == ","
    assert response_body["rowCount"] == 3
    assert response_body["columnCount"] == 3

    assert (tmp_path / f"{file_id}.csv").read_bytes() == content
    assert (tmp_path / f"{file_id}.json").exists()


def test_upload_accepts_windows_1251_with_semicolon(
    client_factory: ClientFactory,
) -> None:
    client = client_factory()

    content = ("product;city\nКофе;Минск\nЧай;Брест\n").encode("cp1251")

    response = client.post(
        "/api/files",
        files={
            "file": (
                "products.csv",
                content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["encoding"] == "Windows-1251"
    assert response.json()["delimiter"] == ";"
    assert response.json()["rowCount"] == 2
    assert response.json()["columnCount"] == 2


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


def test_upload_rejects_empty_csv(
    client_factory: ClientFactory,
    tmp_path: Path,
) -> None:
    client = client_factory()

    response = client.post(
        "/api/files",
        files={
            "file": (
                "empty.csv",
                b"",
                "text/csv",
            )
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "The CSV file is empty."}
    assert list(tmp_path.iterdir()) == []


def test_upload_rejects_unsupported_delimiter(
    client_factory: ClientFactory,
    tmp_path: Path,
) -> None:
    client = client_factory()
    content = b"product\tamount\nCoffee\t10\n"

    response = client.post(
        "/api/files",
        files={
            "file": (
                "tab-separated.csv",
                content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 415
    assert response.json() == {"detail": "The CSV file must use a comma or semicolon delimiter."}
    assert list(tmp_path.iterdir()) == []


def test_upload_rejects_csv_with_inconsistent_rows(
    client_factory: ClientFactory,
    tmp_path: Path,
) -> None:
    client = client_factory()
    content = b"product,amount\nCoffee,10,extra\n"

    response = client.post(
        "/api/files",
        files={
            "file": (
                "broken.csv",
                content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": ("All CSV rows must contain the same number of columns.")}
    assert list(tmp_path.iterdir()) == []
