from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from pydantic import BaseModel

from app.config import FILE_READ_CHUNK_SIZE


class UnsupportedFileTypeError(ValueError):
    pass


class FileTooLargeError(ValueError):
    pass


class StoredFileMetadata(BaseModel):
    file_id: UUID
    file_name: str
    stored_file_name: str
    size_bytes: int
    uploaded_at: datetime


class FileStorageService:
    def __init__(self, storage_dir: Path, max_file_size_bytes: int) -> None:
        self.storage_dir = storage_dir
        self.max_file_size_bytes = max_file_size_bytes
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, uploaded_file: UploadFile) -> StoredFileMetadata:
        original_file_name = Path(uploaded_file.filename or "").name
        self._validate_extension(original_file_name)

        file_id = uuid4()
        stored_file_name = f"{file_id}.csv"
        stored_file_path = self.storage_dir / stored_file_name
        metadata_path = self.storage_dir / f"{file_id}.json"
        size_bytes = 0

        try:
            with stored_file_path.open("wb") as target_file:
                while chunk := await uploaded_file.read(FILE_READ_CHUNK_SIZE):
                    size_bytes += len(chunk)

                    if size_bytes > self.max_file_size_bytes:
                        raise FileTooLargeError(
                            "The uploaded file exceeds the maximum allowed size."
                        )

                    target_file.write(chunk)

            metadata = StoredFileMetadata(
                file_id=file_id,
                file_name=original_file_name,
                stored_file_name=stored_file_name,
                size_bytes=size_bytes,
                uploaded_at=datetime.now(UTC),
            )
            metadata_path.write_text(
                metadata.model_dump_json(indent=2),
                encoding="utf-8",
            )

            return metadata
        except Exception:
            stored_file_path.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)
            raise
        finally:
            await uploaded_file.close()

    @staticmethod
    def _validate_extension(file_name: str) -> None:
        if Path(file_name).suffix.lower() != ".csv":
            raise UnsupportedFileTypeError("Only files with the .csv extension are supported.")
