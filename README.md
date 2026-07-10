# CSV Inspector API

A FastAPI service for uploading, validating, and analyzing CSV files.

## Current stage

The API supports CSV upload, file validation, local storage, file information retrieval, column profiling, and numeric statistics.

## Implemented features

- Health-check endpoint
- CSV upload through multipart/form-data
- `.csv` extension validation
- Maximum file size validation
- Unique file identifiers
- Local CSV storage
- JSON metadata storage
- UTF-8 encoding detection
- Windows-1251 encoding detection
- Comma delimiter detection
- Semicolon delimiter detection
- Empty CSV validation
- Invalid row structure validation
- Binary content validation
- Row and column counting
- File information endpoint
- Column type detection
- Missing value counting
- Unique value counting
- Numeric minimum calculation
- Numeric maximum calculation
- Numeric average calculation
- Numeric median calculation
- Automated API and service tests
- Ruff linting and formatting

## Supported column types

The API currently detects the following column types:

- `number`
- `boolean`
- `datetime`
- `text`
- `empty`

Boolean columns support the following values:

- `true`
- `false`
- `yes`
- `no`

The comparison is case-insensitive.

## Planned features

- Data preview
- Configurable preview row count
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

## API endpoints

### Upload a CSV file

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

### Get file information

```text
GET /api/files/{file_id}
```

Returns metadata about a previously uploaded file.

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

### Get column summary

```text
GET /api/files/{file_id}/summary
```

Returns statistics for all CSV columns.

Example response:

```json
{
  "fileId": "7cb88f0f-7a39-4a6c-a6e7-b2b50b8a761f",
  "fileName": "sales.csv",
  "rowCount": 3,
  "columnCount": 2,
  "delimiter": ",",
  "encoding": "UTF-8",
  "columns": [
    {
      "name": "product",
      "dataType": "text",
      "missingValues": 0,
      "uniqueValues": 2,
      "minimum": null,
      "maximum": null,
      "average": null,
      "median": null
    },
    {
      "name": "amount",
      "dataType": "number",
      "missingValues": 1,
      "uniqueValues": 2,
      "minimum": 10.0,
      "maximum": 20.0,
      "average": 15.0,
      "median": 15.0
    }
  ]
}
```

Missing values are excluded from unique value counts and numeric calculations.

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
│   │   ├── csv_analyzer.py
│   │   ├── csv_reader.py
│   │   └── file_storage.py
│   ├── config.py
│   └── main.py
├── tests/
│   ├── samples/
│   │   └── sales.csv
│   ├── test_csv_analyzer.py
│   ├── test_csv_reader.py
│   ├── test_files_api.py
│   └── test_health.py
├── storage/
│   └── .gitkeep
├── pyproject.toml
├── README.md
└── .gitignore
```