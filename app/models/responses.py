from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiResponseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
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
