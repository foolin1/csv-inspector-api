# CSV Inspector API

A FastAPI service for uploading, validating, previewing, and analyzing CSV files.

## Current stage

The API supports CSV upload, file validation, local storage, file information retrieval, column profiling, row preview, and detailed statistics for individual columns.

## Implemented features

- Health-check endpoint
- CSV upload through multipart/form-data
- `.csv` extension validation
- Maximum file size validation
- UTF-8 encoding detection
- Windows-1251 encoding detection
- Comma delimiter detection
- Semicolon delimiter detection
- Empty CSV validation
- Invalid row structure validation
- Binary content validation
- Unique file identifiers
- Local CSV storage
- JSON metadata storage
- Row and column counting
- File information endpoint
- Column type detection
- Missing value counting
- Unique value counting
- Numeric minimum calculation
- Numeric maximum calculation
- Numeric average calculation
- Numeric median calculation
- CSV row preview
- Configurable preview row count
- Detailed statistics for one column
- Automated API and service tests
- Ruff linting and formatting

## Supported column types

The API detects the following column types:

- `number`
- `boolean`
- `datetime`
- `text`
- `empty`

Boolean columns support:

- `true`
- `false`
- `yes`
- `no`

The comparison is case-insensitive.

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

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Health-check:

```text
http://127.0.0.1:8000/health
```

## API endpoints

### Upload a CSV file

```text
POST /api/files
```

The request must contain a CSV file in the `file` form field.

### Get file information

```text
GET /api/files/{file_id}
```

Returns metadata about an uploaded CSV file.

### Get summary for all columns

```text
GET /api/files/{file_id}/summary
```

Returns data types, missing value counts, unique value counts, and numeric statistics.

### Preview CSV rows

```text
GET /api/files/{file_id}/preview?rows=10
```

The `rows` parameter must be between 1 and 100.

Example response:

```json
{
  "fileId": "7cb88f0f-7a39-4a6c-a6e7-b2b50b8a761f",
  "fileName": "sales.csv",
  "requestedRows": 2,
  "returnedRows": 2,
  "columns": [
    "product",
    "amount"
  ],
  "rows": [
    {
      "product": "Coffee",
      "amount": "10"
    },
    {
      "product": "Tea",
      "amount": null
    }
  ]
}
```

### Get details for one column

```text
GET /api/files/{file_id}/columns/{column_name}
```

Example:

```text
GET /api/files/{file_id}/columns/amount
```

Example response:

```json
{
  "fileId": "7cb88f0f-7a39-4a6c-a6e7-b2b50b8a761f",
  "fileName": "sales.csv",
  "column": {
    "name": "amount",
    "dataType": "number",
    "missingValues": 1,
    "uniqueValues": 2,
    "minimum": 10.0,
    "maximum": 20.0,
    "average": 15.0,
    "median": 15.0
  }
}
```

## Run tests

```powershell
python -m pytest
```

## Check code quality

```powershell
ruff check .
ruff format --check .
```

## Planned features

- Uploaded file deletion
- Unified error response format
- Additional automated tests
- GitHub Actions
- Final project documentation

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