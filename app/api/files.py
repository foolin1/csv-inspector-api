from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import MAX_FILE_SIZE_BYTES, STORAGE_DIR
from app.models.responses import FileUploadResponse
from app.services.csv_reader import (
    EmptyCsvError,
    InvalidCsvError,
    UnsupportedDelimiterError,
    UnsupportedEncodingError,
)
from app.services.file_storage import (
    FileStorageService,
    FileTooLargeError,
    UnsupportedFileTypeError,
)

router = APIRouter(prefix="/api/files", tags=["Files"])

file_storage_service = FileStorageService(
    storage_dir=STORAGE_DIR,
    max_file_size_bytes=MAX_FILE_SIZE_BYTES,
)


def get_file_storage_service() -> FileStorageService:
    return file_storage_service


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

    return FileUploadResponse(
        file_id=metadata.file_id,
        file_name=metadata.file_name,
        size_bytes=metadata.size_bytes,
        uploaded_at=metadata.uploaded_at,
        encoding=metadata.encoding,
        delimiter=metadata.delimiter,
        row_count=metadata.row_count,
        column_count=metadata.column_count,
    )
