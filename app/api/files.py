from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Query,
    Response,
    UploadFile,
    status,
)

from app.api.errors import ApiError
from app.config import (
    MAX_FILE_SIZE_BYTES,
    MAX_PREVIEW_ROWS,
    STORAGE_DIR,
)
from app.models.responses import (
    ColumnDetailsResponse,
    ColumnSummaryResponse,
    FileInfoResponse,
    FilePreviewResponse,
    FileSummaryResponse,
    FileUploadResponse,
)
from app.services.csv_analyzer import (
    ColumnAnalysis,
    ColumnNotFoundError,
    CsvAnalyzerService,
)
from app.services.csv_reader import (
    EmptyCsvError,
    InvalidCsvError,
    UnsupportedDelimiterError,
    UnsupportedEncodingError,
)
from app.services.file_storage import (
    FileStorageService,
    FileTooLargeError,
    StoredFileDeletionError,
    StoredFileMetadataError,
    StoredFileNotFoundError,
    UnsupportedFileTypeError,
)

router = APIRouter(
    prefix="/api/files",
    tags=["Files"],
)

file_storage_service = FileStorageService(
    storage_dir=STORAGE_DIR,
    max_file_size_bytes=MAX_FILE_SIZE_BYTES,
)

csv_analyzer_service = CsvAnalyzerService()


def get_file_storage_service() -> FileStorageService:
    return file_storage_service


def get_csv_analyzer_service() -> CsvAnalyzerService:
    return csv_analyzer_service


def build_column_response(
    column: ColumnAnalysis,
) -> ColumnSummaryResponse:
    numeric_statistics = column.numeric_statistics

    return ColumnSummaryResponse(
        name=column.name,
        data_type=column.data_type,
        missing_values=column.missing_values,
        unique_values=column.unique_values,
        minimum=(numeric_statistics.minimum if numeric_statistics else None),
        maximum=(numeric_statistics.maximum if numeric_statistics else None),
        average=(numeric_statistics.average if numeric_statistics else None),
        median=(numeric_statistics.median if numeric_statistics else None),
    )


@router.post(
    "",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a CSV file",
)
async def upload_file(
    file: Annotated[
        UploadFile,
        File(description="CSV file to upload"),
    ],
    storage_service: Annotated[
        FileStorageService,
        Depends(get_file_storage_service),
    ],
) -> FileUploadResponse:
    try:
        metadata = await storage_service.save(file)
    except UnsupportedFileTypeError as exc:
        raise ApiError(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="unsupported_file_type",
            message=str(exc),
        ) from exc
    except FileTooLargeError as exc:
        raise ApiError(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            code="file_too_large",
            message=str(exc),
        ) from exc
    except UnsupportedEncodingError as exc:
        raise ApiError(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="unsupported_encoding",
            message=str(exc),
        ) from exc
    except UnsupportedDelimiterError as exc:
        raise ApiError(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="unsupported_delimiter",
            message=str(exc),
        ) from exc
    except EmptyCsvError as exc:
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="empty_csv",
            message=str(exc),
        ) from exc
    except InvalidCsvError as exc:
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="invalid_csv",
            message=str(exc),
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
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="file_not_found",
            message=str(exc),
        ) from exc
    except StoredFileMetadataError as exc:
        raise ApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="stored_metadata_invalid",
            message=str(exc),
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
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="file_not_found",
            message=str(exc),
        ) from exc
    except StoredFileMetadataError as exc:
        raise ApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="stored_metadata_invalid",
            message=str(exc),
        ) from exc

    analysis = analyzer_service.analyze(
        file_path=file_path,
        encoding=metadata.encoding,
        delimiter=metadata.delimiter,
    )

    return FileSummaryResponse(
        file_id=metadata.file_id,
        file_name=metadata.file_name,
        row_count=metadata.row_count,
        column_count=metadata.column_count,
        delimiter=metadata.delimiter,
        encoding=metadata.encoding,
        columns=[build_column_response(column) for column in analysis.columns],
    )


@router.get(
    "/{file_id}/preview",
    response_model=FilePreviewResponse,
    summary="Preview CSV rows",
)
def get_file_preview(
    file_id: UUID,
    storage_service: Annotated[
        FileStorageService,
        Depends(get_file_storage_service),
    ],
    analyzer_service: Annotated[
        CsvAnalyzerService,
        Depends(get_csv_analyzer_service),
    ],
    rows: Annotated[
        int,
        Query(
            ge=1,
            le=MAX_PREVIEW_ROWS,
            description="Number of rows to return",
        ),
    ] = 10,
) -> FilePreviewResponse:
    try:
        metadata = storage_service.get_metadata(file_id)
        file_path = storage_service.get_file_path(file_id)
    except StoredFileNotFoundError as exc:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="file_not_found",
            message=str(exc),
        ) from exc
    except StoredFileMetadataError as exc:
        raise ApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="stored_metadata_invalid",
            message=str(exc),
        ) from exc

    preview = analyzer_service.preview(
        file_path=file_path,
        encoding=metadata.encoding,
        delimiter=metadata.delimiter,
        row_limit=rows,
    )

    return FilePreviewResponse(
        file_id=metadata.file_id,
        file_name=metadata.file_name,
        requested_rows=rows,
        returned_rows=len(preview.rows),
        columns=preview.columns,
        rows=preview.rows,
    )


@router.get(
    "/{file_id}/columns/{column_name}",
    response_model=ColumnDetailsResponse,
    summary="Get detailed statistics for one column",
)
def get_column_details(
    file_id: UUID,
    column_name: str,
    storage_service: Annotated[
        FileStorageService,
        Depends(get_file_storage_service),
    ],
    analyzer_service: Annotated[
        CsvAnalyzerService,
        Depends(get_csv_analyzer_service),
    ],
) -> ColumnDetailsResponse:
    try:
        metadata = storage_service.get_metadata(file_id)
        file_path = storage_service.get_file_path(file_id)
    except StoredFileNotFoundError as exc:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="file_not_found",
            message=str(exc),
        ) from exc
    except StoredFileMetadataError as exc:
        raise ApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="stored_metadata_invalid",
            message=str(exc),
        ) from exc

    try:
        column = analyzer_service.analyze_column(
            file_path=file_path,
            encoding=metadata.encoding,
            delimiter=metadata.delimiter,
            column_name=column_name,
        )
    except ColumnNotFoundError as exc:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="column_not_found",
            message=str(exc),
        ) from exc

    return ColumnDetailsResponse(
        file_id=metadata.file_id,
        file_name=metadata.file_name,
        column=build_column_response(column),
    )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an uploaded CSV file",
)
def delete_file(
    file_id: UUID,
    storage_service: Annotated[
        FileStorageService,
        Depends(get_file_storage_service),
    ],
) -> Response:
    try:
        storage_service.delete(file_id)
    except StoredFileNotFoundError as exc:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="file_not_found",
            message=str(exc),
        ) from exc
    except StoredFileMetadataError as exc:
        raise ApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="stored_metadata_invalid",
            message=str(exc),
        ) from exc
    except StoredFileDeletionError as exc:
        raise ApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="file_deletion_failed",
            message=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
