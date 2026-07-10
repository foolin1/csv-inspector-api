from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiResponseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class FileUploadResponse(ApiResponseModel):
    file_id: UUID
    file_name: str
    size_bytes: int
    uploaded_at: datetime
    encoding: str
    delimiter: str
    row_count: int
    column_count: int


class FileInfoResponse(FileUploadResponse):
    pass


class ColumnSummaryResponse(ApiResponseModel):
    name: str
    data_type: str
    missing_values: int
    unique_values: int
    minimum: float | None = None
    maximum: float | None = None
    average: float | None = None
    median: float | None = None


class FileSummaryResponse(ApiResponseModel):
    file_id: UUID
    file_name: str
    row_count: int
    column_count: int
    delimiter: str
    encoding: str
    columns: list[ColumnSummaryResponse]


class FilePreviewResponse(ApiResponseModel):
    file_id: UUID
    file_name: str
    requested_rows: int
    returned_rows: int
    columns: list[str]
    rows: list[dict[str, str | None]]


class ColumnDetailsResponse(ApiResponseModel):
    file_id: UUID
    file_name: str
    column: ColumnSummaryResponse
