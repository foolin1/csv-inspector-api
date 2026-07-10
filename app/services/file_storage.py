from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from pydantic import BaseModel, ValidationError

from app.config import FILE_READ_CHUNK_SIZE
from app.services.csv_reader import CsvReaderService


class UnsupportedFileTypeError(ValueError):
    pass


class FileTooLargeError(ValueError):
    pass


class StoredFileNotFoundError(FileNotFoundError):
    pass


class StoredFileMetadataError(ValueError):
    pass


class StoredFileDeletionError(OSError):
    pass


class StoredFileMetadata(BaseModel):
    file_id: UUID
    file_name: str
    stored_file_name: str
    size_bytes: int
    uploaded_at: datetime
    encoding: str
    delimiter: str
    row_count: int
    column_count: int


class FileStorageService:
    def __init__(
        self,
        storage_dir: Path,
        max_file_size_bytes: int,
        csv_reader_service: CsvReaderService | None = None,
    ) -> None:
        self.storage_dir = storage_dir
        self.max_file_size_bytes = max_file_size_bytes
        self.csv_reader_service = csv_reader_service or CsvReaderService()
        self.storage_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    async def save(
        self,
        uploaded_file: UploadFile,
    ) -> StoredFileMetadata:
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

            csv_info = self.csv_reader_service.inspect(stored_file_path)

            metadata = StoredFileMetadata(
                file_id=file_id,
                file_name=original_file_name,
                stored_file_name=stored_file_name,
                size_bytes=size_bytes,
                uploaded_at=datetime.now(UTC),
                encoding=csv_info.encoding,
                delimiter=csv_info.delimiter,
                row_count=csv_info.row_count,
                column_count=csv_info.column_count,
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

    def get_metadata(
        self,
        file_id: UUID,
    ) -> StoredFileMetadata:
        metadata_path = self.storage_dir / f"{file_id}.json"

        if not metadata_path.exists():
            raise StoredFileNotFoundError("The requested file was not found.")

        try:
            return StoredFileMetadata.model_validate_json(metadata_path.read_text(encoding="utf-8"))
        except (
            OSError,
            ValidationError,
            ValueError,
        ) as exc:
            raise StoredFileMetadataError("The stored file metadata is invalid.") from exc

    def get_file_path(
        self,
        file_id: UUID,
    ) -> Path:
        metadata = self.get_metadata(file_id)
        file_path = self.storage_dir / metadata.stored_file_name

        if not file_path.exists():
            raise StoredFileNotFoundError("The requested file was not found.")

        return file_path

    def delete(
        self,
        file_id: UUID,
    ) -> None:
        metadata = self.get_metadata(file_id)

        metadata_path = self.storage_dir / f"{file_id}.json"
        file_path = self.storage_dir / metadata.stored_file_name

        if not file_path.exists():
            raise StoredFileNotFoundError("The requested file was not found.")

        try:
            file_path.unlink()
            metadata_path.unlink()
        except OSError as exc:
            raise StoredFileDeletionError("The stored file could not be deleted.") from exc

    @staticmethod
    def _validate_extension(
        file_name: str,
    ) -> None:
        if Path(file_name).suffix.lower() != ".csv":
            raise UnsupportedFileTypeError("Only files with the .csv extension are supported.")
