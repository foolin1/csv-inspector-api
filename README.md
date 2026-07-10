# CSV Inspector API

A FastAPI service for uploading, validating, and analyzing CSV files.

## Current stage

The API supports CSV upload, local storage, encoding detection, delimiter detection, structural validation, metadata storage, automated tests, and code quality checks.

## Implemented features

- Health-check endpoint
- CSV upload through multipart/form-data
- `.csv` extension validation
- Maximum file size validation
- Unique file identifiers
- Local file storage
- JSON metadata storage
- UTF-8 encoding detection
- Windows-1251 encoding detection
- Comma delimiter detection
- Semicolon delimiter detection
- Empty CSV validation
- Invalid row structure validation
- Binary content validation
- Row and column counting
- Automated API and service tests
- Ruff linting and formatting

## Planned features

- File information endpoint
- Column profiling
- Missing value statistics
- Unique value statistics
- Numeric column statistics
- Data preview
- Detailed statistics for one column
- Uploaded file deletion
- Unified error responses
- GitHub Actions

## Requirements

- Python 3.12+
- Git

## Local setup

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run the application

```powershell
python -m uvicorn app.main:app --reload
```

Open the Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Health-check endpoint:

```text
http://127.0.0.1:8000/health
```

## Upload a file

Use the following endpoint:

```text
POST /api/files
```

The request must contain a CSV file in the `file` form field.

Supported encodings:

- UTF-8
- Windows-1251

Supported delimiters:

- comma
- semicolon

Example response:

```json
{
  "fileId": "7cb88f0f-7a39-4a6c-a6e7-b2b50b8a761f",
  "fileName": "sales.csv",
  "sizeBytes": 87,
  "uploadedAt": "2026-07-10T10:30:00Z",
  "encoding": "UTF-8",
  "delimiter": ",",
  "rowCount": 3,
  "columnCount": 3
}
```

Uploaded files and metadata are stored in the local `storage` directory.

Invalid files are removed automatically.

## Run tests

```powershell
python -m pytest
```

## Check code quality

```powershell
ruff check .
ruff format --check .
```

## Project structure

```text
csv-inspector-api/
├── app/
│   ├── api/
│   │   └── files.py
│   ├── models/
│   │   └── responses.py
│   ├── services/
│   │   ├── csv_reader.py
│   │   └── file_storage.py
│   ├── config.py
│   └── main.py
├── tests/
│   ├── samples/
│   │   └── sales.csv
│   ├── test_csv_reader.py
│   ├── test_files_api.py
│   └── test_health.py
├── storage/
│   └── .gitkeep
├── pyproject.toml
├── README.md
└── .gitignore
```