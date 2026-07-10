from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import MAX_FILE_SIZE_BYTES, STORAGE_DIR
from app.models.responses import (
    ColumnSummaryResponse,
    FileInfoResponse,
    FileSummaryResponse,
    FileUploadResponse,
)
from app.services.csv_analyzer import CsvAnalyzerService
from app.services.csv_reader import (
    EmptyCsvError,
    InvalidCsvError,
    UnsupportedDelimiterError,
    UnsupportedEncodingError,
)
from app.services.file_storage import (
    FileStorageService,
    FileTooLargeError,
    StoredFileMetadataError,
    StoredFileNotFoundError,
    UnsupportedFileTypeError,
)

router = APIRouter(prefix="/api/files", tags=["Files"])

file_storage_service = FileStorageService(
    storage_dir=STORAGE_DIR,
    max_file_size_bytes=MAX_FILE_SIZE_BYTES,
)
csv_analyzer_service = CsvAnalyzerService()


def get_file_storage_service() -> FileStorageService:
    return file_storage_service


def get_csv_analyzer_service() -> CsvAnalyzerService:
    return csv_analyzer_service


@router.post(
    "",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a CSV file",
)
async def upload_file(
    file: Annotated[UploadFile, File(description="CSV file to upload")],
    storage_service: Annotated[
        FileStorageService,
        Depends(get_file_storage_service),
    ],
) -> FileUploadResponse:
    try:
        metadata = await storage_service.save(file)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except (UnsupportedEncodingError, UnsupportedDelimiterError) as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc
    except (EmptyCsvError, InvalidCsvError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return FileUploadResponse.model_validate(metadata)


@router.get(
    "/{file_id}",
    response_model=FileInfoResponse,
    summary="Get uploaded file information",
)
def get_file_information(
    file_id: UUID,
    storage_service: Annotated[
        FileStorageService,
        Depends(get_file_storage_service),
    ],
) -> FileInfoResponse:
    try:
        metadata = storage_service.get_metadata(file_id)
    except StoredFileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except StoredFileMetadataError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return FileInfoResponse.model_validate(metadata)


@router.get(
    "/{file_id}/summary",
    response_model=FileSummaryResponse,
    summary="Get CSV column summary",
)
def get_file_summary(
    file_id: UUID,
    storage_service: Annotated[
        FileStorageService,
        Depends(get_file_storage_service),
    ],
    analyzer_service: Annotated[
        CsvAnalyzerService,
        Depends(get_csv_analyzer_service),
    ],
) -> FileSummaryResponse:
    try:
        metadata = storage_service.get_metadata(file_id)
        file_path = storage_service.get_file_path(file_id)
    except StoredFileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except StoredFileMetadataError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    analysis = analyzer_service.analyze(
        file_path=file_path,
        encoding=metadata.encoding,
        delimiter=metadata.delimiter,
    )

    columns = []
    for column in analysis.columns:
        numeric_statistics = column.numeric_statistics
        columns.append(
            ColumnSummaryResponse(
                name=column.name,
                data_type=column.data_type,
                missing_values=column.missing_values,
                unique_values=column.unique_values,
                minimum=(numeric_statistics.minimum if numeric_statistics else None),
                maximum=(numeric_statistics.maximum if numeric_statistics else None),
                average=(numeric_statistics.average if numeric_statistics else None),
                median=(numeric_statistics.median if numeric_statistics else None),
            )
        )

    return FileSummaryResponse(
        file_id=metadata.file_id,
        file_name=metadata.file_name,
        row_count=metadata.row_count,
        column_count=metadata.column_count,
        delimiter=metadata.delimiter,
        encoding=metadata.encoding,
        columns=columns,
    )
