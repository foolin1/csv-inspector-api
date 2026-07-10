from pathlib import Path

APP_NAME = "CSV Inspector API"
APP_VERSION = "0.3.0"
APP_DESCRIPTION = "REST API for uploading and analyzing CSV files."

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_PREVIEW_ROWS = 100
FILE_READ_CHUNK_SIZE = 1024 * 1024
