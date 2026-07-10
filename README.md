# CSV Inspector API

[![Python CI](https://github.com/foolin1/csv-inspector-api/actions/workflows/python.yml/badge.svg?branch=main)](https://github.com/foolin1/csv-inspector-api/actions/workflows/python.yml)

A REST API for uploading, validating, previewing, and analyzing CSV files.

The service helps inspect an unfamiliar CSV file without opening it in Excel or writing a separate data-processing script. It detects the file structure, determines column types, counts missing and unique values, and calculates numeric statistics.

## Features

- CSV upload through `multipart/form-data`
- Unique identifiers for uploaded files
- Local storage of files and metadata
- Maximum file size validation
- `.csv` extension validation
- UTF-8 encoding support
- Windows-1251 encoding support
- Comma delimiter support
- Semicolon delimiter support
- Empty file validation
- Invalid row structure validation
- Binary content validation
- Row and column counting
- File metadata retrieval
- Column type detection
- Missing value counting
- Unique value counting
- Numeric minimum, maximum, average, and median
- Preview of the first N rows
- Detailed analysis of one selected column
- Uploaded file deletion
- Unified API error responses
- Automated tests
- Ruff linting and formatting
- GitHub Actions continuous integration

## Technology stack

- Python 3.12+
- FastAPI
- Pandas
- Pydantic
- Uvicorn
- Pytest
- HTTPX / FastAPI TestClient
- Ruff
- GitHub Actions

## Architecture

```text
HTTP request
    |
    v
FastAPI endpoint
    |
    v
File validation
    |
    +----> FileStorageService
    |          |
    |          +----> Local CSV storage
    |          |
    |          +----> JSON metadata storage
    |
    +----> CsvReaderService
    |          |
    |          +----> Encoding detection
    |          |
    |          +----> Delimiter detection
    |          |
    |          +----> Structural validation
    |
    +----> CsvAnalyzerService
               |
               +----> Pandas DataFrame
               |
               +----> Column statistics
               |
               +----> Preview data
```

## Supported files

### Encodings

- UTF-8
- UTF-8 with BOM
- Windows-1251

### Delimiters

- Comma: `,`
- Semicolon: `;`

### Limits

- Maximum file size: 10 MB
- Maximum preview size: 100 rows

## Supported column types

The service detects the following data types:

- `number`
- `boolean`
- `datetime`
- `text`
- `empty`

Boolean columns support these values:

- `true`
- `false`
- `yes`
- `no`

Boolean detection is case-insensitive.

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Check service availability |
| `POST` | `/api/files` | Upload a CSV file |
| `GET` | `/api/files/{file_id}` | Get uploaded file metadata |
| `GET` | `/api/files/{file_id}/summary` | Get statistics for all columns |
| `GET` | `/api/files/{file_id}/preview` | Preview the first N rows |
| `GET` | `/api/files/{file_id}/columns/{column_name}` | Analyze one column |
| `DELETE` | `/api/files/{file_id}` | Delete a file and its metadata |

## Project structure

```text
csv-inspector-api/
├── .github/
│   └── workflows/
│       └── python.yml
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── errors.py
│   │   └── files.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── responses.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── csv_analyzer.py
│   │   ├── csv_reader.py
│   │   └── file_storage.py
│   ├── __init__.py
│   ├── config.py
│   └── main.py
├── storage/
│   └── .gitkeep
├── tests/
│   ├── samples/
│   │   └── sales.csv
│   ├── test_csv_analyzer.py
│   ├── test_csv_reader.py
│   ├── test_error_handlers.py
│   ├── test_files_api.py
│   └── test_health.py
├── .gitignore
├── pyproject.toml
└── README.md
```

## Local installation

### 1. Clone the repository

```bash
git clone https://github.com/foolin1/csv-inspector-api.git
cd csv-inspector-api
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Running the application

```bash
python -m uvicorn app.main:app --reload
```

The application will be available at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Alternative ReDoc documentation:

```text
http://127.0.0.1:8000/redoc
```

Health-check:

```text
http://127.0.0.1:8000/health
```

## Usage

### Upload a CSV file

```text
POST /api/files
```

The request must contain a file in the `file` form field.

Example using cURL:

```bash
curl -X POST \
  "http://127.0.0.1:8000/api/files" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@tests/samples/sales.csv;type=text/csv"
```

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

The returned `fileId` is used in the other endpoints.

### Get file information

```text
GET /api/files/{file_id}
```

Example:

```bash
curl "http://127.0.0.1:8000/api/files/7cb88f0f-7a39-4a6c-a6e7-b2b50b8a761f"
```

### Get statistics for all columns

```text
GET /api/files/{file_id}/summary
```

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

### Preview CSV rows

```text
GET /api/files/{file_id}/preview?rows=10
```

The `rows` parameter must be between 1 and 100. Its default value is 10.

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

### Analyze one column

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

### Delete an uploaded file

```text
DELETE /api/files/{file_id}
```

A successful deletion returns:

```text
204 No Content
```

Both the CSV file and its JSON metadata are removed.

## Error format

All controlled API errors use the same JSON structure:

```json
{
  "error": {
    "code": "file_not_found",
    "message": "The requested file was not found.",
    "details": null
  }
}
```

Validation errors can contain additional details:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": [
      {
        "field": "query.rows",
        "message": "Input should be greater than or equal to 1",
        "type": "greater_than_equal"
      }
    ]
  }
}
```

Common error codes:

| HTTP status | Error code | Description |
|---|---|---|
| `413` | `file_too_large` | File exceeds the size limit |
| `415` | `unsupported_file_type` | File does not have a `.csv` extension |
| `415` | `unsupported_encoding` | Encoding is not supported |
| `415` | `unsupported_delimiter` | Delimiter is not supported |
| `422` | `empty_csv` | CSV file is empty |
| `422` | `invalid_csv` | CSV structure is invalid |
| `422` | `validation_error` | Request parameters are invalid |
| `404` | `file_not_found` | File does not exist |
| `404` | `column_not_found` | Column does not exist |

## Local storage

Uploaded files are stored in the local `storage` directory.

Each upload creates two files:

```text
storage/
├── {file_id}.csv
└── {file_id}.json
```

The JSON file stores:

- original file name;
- stored file name;
- file size;
- upload date;
- encoding;
- delimiter;
- row count;
- column count.

Uploaded files are excluded from Git. Only `storage/.gitkeep` is committed.

## Running tests

```bash
python -m pytest
```

The project contains automated tests for:

- valid file uploads;
- invalid extensions;
- oversized files;
- empty files;
- unsupported delimiters;
- invalid CSV structures;
- UTF-8 files;
- Windows-1251 files;
- row and column counting;
- column type detection;
- missing and unique values;
- numeric statistics;
- previews;
- unknown files;
- unknown columns;
- file deletion;
- validation errors;
- unified error responses.

## Code quality

Run Ruff linting:

```bash
ruff check .
```

Check formatting:

```bash
ruff format --check .
```

Automatically format the project:

```bash
ruff format .
```

## Continuous integration

GitHub Actions runs automatically for:

- pushes to `main`;
- pull requests targeting `main`;
- manual workflow runs.

The workflow performs:

1. Python 3.12 setup;
2. dependency installation;
3. Ruff linting;
4. Ruff formatting validation;
5. automated tests.

## Limitations

The first release intentionally does not include:

- user registration and authentication;
- a permanent database;
- cloud storage;
- Excel or Parquet support;
- editing uploaded data;
- background task queues;
- large-scale distributed file processing;
- a separate frontend.

The application is intended as a compact backend portfolio project and a demonstration of file handling, API design, validation, testing, and basic data analysis with Pandas.