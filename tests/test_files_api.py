from collections.abc import Iterator
from pathlib import Path
from typing import Protocol
from uuid import uuid4

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
def client_factory(
    tmp_path: Path,
) -> Iterator[ClientFactory]:
    clients: list[TestClient] = []

    def create_client(
        max_file_size_bytes: int = 1024,
    ) -> TestClient:
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


def upload_csv(
    client: TestClient,
    content: bytes,
    file_name: str = "sales.csv",
) -> dict:
    response = client.post(
        "/api/files",
        files={
            "file": (
                file_name,
                content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 201

    return response.json()


def assert_api_error(
    response,
    status_code: int,
    code: str,
    message: str,
) -> None:
    assert response.status_code == status_code

    assert response.json() == {
        "error": {
            "code": code,
            "message": message,
            "details": None,
        }
    }


def test_upload_csv_saves_file_and_returns_metadata(
    client_factory: ClientFactory,
    tmp_path: Path,
) -> None:
    client = client_factory()

    content = (SAMPLES_DIR / "sales.csv").read_bytes()

    response_body = upload_csv(
        client,
        content,
    )

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

    response_body = upload_csv(
        client,
        content,
        "products.csv",
    )

    assert response_body["encoding"] == "Windows-1251"
    assert response_body["delimiter"] == ";"
    assert response_body["rowCount"] == 2
    assert response_body["columnCount"] == 2


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

    assert_api_error(
        response=response,
        status_code=415,
        code="unsupported_file_type",
        message=("Only files with the .csv extension are supported."),
    )

    assert list(tmp_path.iterdir()) == []


def test_upload_rejects_file_larger_than_limit(
    client_factory: ClientFactory,
    tmp_path: Path,
) -> None:
    client = client_factory(
        max_file_size_bytes=10,
    )

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

    assert_api_error(
        response=response,
        status_code=413,
        code="file_too_large",
        message=("The uploaded file exceeds the maximum allowed size."),
    )

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

    assert_api_error(
        response=response,
        status_code=422,
        code="empty_csv",
        message="The CSV file is empty.",
    )

    assert list(tmp_path.iterdir()) == []


def test_upload_rejects_unsupported_delimiter(
    client_factory: ClientFactory,
    tmp_path: Path,
) -> None:
    client = client_factory()

    response = client.post(
        "/api/files",
        files={
            "file": (
                "tab-separated.csv",
                b"product\tamount\nCoffee\t10\n",
                "text/csv",
            )
        },
    )

    assert_api_error(
        response=response,
        status_code=415,
        code="unsupported_delimiter",
        message=("The CSV file must use a comma or semicolon delimiter."),
    )

    assert list(tmp_path.iterdir()) == []


def test_upload_rejects_csv_with_inconsistent_rows(
    client_factory: ClientFactory,
    tmp_path: Path,
) -> None:
    client = client_factory()

    response = client.post(
        "/api/files",
        files={
            "file": (
                "broken.csv",
                b"product,amount\nCoffee,10,extra\n",
                "text/csv",
            )
        },
    )

    assert_api_error(
        response=response,
        status_code=422,
        code="invalid_csv",
        message=("All CSV rows must contain the same number of columns."),
    )

    assert list(tmp_path.iterdir()) == []


def test_upload_without_file_returns_validation_error(
    client_factory: ClientFactory,
) -> None:
    client = client_factory()

    response = client.post("/api/files")

    assert response.status_code == 422

    body = response.json()

    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "Request validation failed."
    assert body["error"]["details"]
    assert body["error"]["details"][0]["field"] == "body.file"


def test_get_file_information_returns_stored_metadata(
    client_factory: ClientFactory,
) -> None:
    client = client_factory()

    uploaded = upload_csv(
        client,
        b"name,amount\nCoffee,10\nTea,20\n",
    )

    response = client.get(f"/api/files/{uploaded['fileId']}")

    assert response.status_code == 200
    assert response.json() == uploaded


def test_get_file_information_returns_404_for_unknown_file(
    client_factory: ClientFactory,
) -> None:
    client = client_factory()

    response = client.get(f"/api/files/{uuid4()}")

    assert_api_error(
        response=response,
        status_code=404,
        code="file_not_found",
        message="The requested file was not found.",
    )


def test_get_file_summary_returns_column_statistics(
    client_factory: ClientFactory,
) -> None:
    client = client_factory()

    content = (
        b"product,amount,active,created_at\n"
        b"Coffee,10,true,2026-07-01\n"
        b"Tea,20,false,2026-07-02\n"
        b"Coffee,,true,2026-07-03\n"
    )

    uploaded = upload_csv(
        client,
        content,
    )

    response = client.get(f"/api/files/{uploaded['fileId']}/summary")

    assert response.status_code == 200

    body = response.json()

    assert body["fileId"] == uploaded["fileId"]
    assert body["rowCount"] == 3
    assert body["columnCount"] == 4

    columns = {column["name"]: column for column in body["columns"]}

    assert columns["product"]["dataType"] == "text"
    assert columns["product"]["uniqueValues"] == 2

    assert columns["amount"] == {
        "name": "amount",
        "dataType": "number",
        "missingValues": 1,
        "uniqueValues": 2,
        "minimum": 10.0,
        "maximum": 20.0,
        "average": 15.0,
        "median": 15.0,
    }

    assert columns["active"]["dataType"] == "boolean"
    assert columns["created_at"]["dataType"] == "datetime"


def test_get_file_summary_returns_404_for_unknown_file(
    client_factory: ClientFactory,
) -> None:
    client = client_factory()

    response = client.get(f"/api/files/{uuid4()}/summary")

    assert_api_error(
        response=response,
        status_code=404,
        code="file_not_found",
        message="The requested file was not found.",
    )


def test_get_file_preview_returns_requested_rows(
    client_factory: ClientFactory,
) -> None:
    client = client_factory()

    content = b"product,amount\nCoffee,10\nTea,\nBread,5\n"

    uploaded = upload_csv(
        client,
        content,
    )

    response = client.get(f"/api/files/{uploaded['fileId']}/preview?rows=2")

    assert response.status_code == 200

    assert response.json() == {
        "fileId": uploaded["fileId"],
        "fileName": "sales.csv",
        "requestedRows": 2,
        "returnedRows": 2,
        "columns": [
            "product",
            "amount",
        ],
        "rows": [
            {
                "product": "Coffee",
                "amount": "10",
            },
            {
                "product": "Tea",
                "amount": None,
            },
        ],
    }


def test_get_file_preview_rejects_invalid_row_count(
    client_factory: ClientFactory,
) -> None:
    client = client_factory()

    uploaded = upload_csv(
        client,
        b"product,amount\nCoffee,10\n",
    )

    response = client.get(f"/api/files/{uploaded['fileId']}/preview?rows=0")

    assert response.status_code == 422

    body = response.json()

    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "Request validation failed."
    assert body["error"]["details"][0]["field"] == "query.rows"


def test_get_file_preview_returns_404_for_unknown_file(
    client_factory: ClientFactory,
) -> None:
    client = client_factory()

    response = client.get(f"/api/files/{uuid4()}/preview?rows=2")

    assert_api_error(
        response=response,
        status_code=404,
        code="file_not_found",
        message="The requested file was not found.",
    )


def test_get_column_details_returns_selected_column_statistics(
    client_factory: ClientFactory,
) -> None:
    client = client_factory()

    content = b"product,total amount\nCoffee,10\nTea,20\nBread,\n"

    uploaded = upload_csv(
        client,
        content,
    )

    response = client.get(f"/api/files/{uploaded['fileId']}/columns/total%20amount")

    assert response.status_code == 200

    assert response.json() == {
        "fileId": uploaded["fileId"],
        "fileName": "sales.csv",
        "column": {
            "name": "total amount",
            "dataType": "number",
            "missingValues": 1,
            "uniqueValues": 2,
            "minimum": 10.0,
            "maximum": 20.0,
            "average": 15.0,
            "median": 15.0,
        },
    }


def test_get_column_details_returns_404_for_unknown_column(
    client_factory: ClientFactory,
) -> None:
    client = client_factory()

    uploaded = upload_csv(
        client,
        b"product,amount\nCoffee,10\n",
    )

    response = client.get(f"/api/files/{uploaded['fileId']}/columns/unknown")

    assert_api_error(
        response=response,
        status_code=404,
        code="column_not_found",
        message='The column "unknown" was not found.',
    )


def test_delete_file_removes_csv_and_metadata(
    client_factory: ClientFactory,
    tmp_path: Path,
) -> None:
    client = client_factory()

    uploaded = upload_csv(
        client,
        b"product,amount\nCoffee,10\n",
    )

    file_id = uploaded["fileId"]
    csv_path = tmp_path / f"{file_id}.csv"
    metadata_path = tmp_path / f"{file_id}.json"

    assert csv_path.exists()
    assert metadata_path.exists()

    response = client.delete(f"/api/files/{file_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert not csv_path.exists()
    assert not metadata_path.exists()

    get_response = client.get(f"/api/files/{file_id}")

    assert_api_error(
        response=get_response,
        status_code=404,
        code="file_not_found",
        message="The requested file was not found.",
    )


def test_delete_file_returns_404_for_unknown_file(
    client_factory: ClientFactory,
) -> None:
    client = client_factory()

    response = client.delete(f"/api/files/{uuid4()}")

    assert_api_error(
        response=response,
        status_code=404,
        code="file_not_found",
        message="The requested file was not found.",
    )
