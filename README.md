# CSV Inspector API

A small FastAPI service for uploading and analyzing CSV files.

## Current stage

The project skeleton, health-check endpoint, automated tests, and development tools are configured.

## Planned features

- CSV file upload
- File extension and size validation
- UTF-8 and Windows-1251 encoding support
- Comma and semicolon delimiter detection
- Column profiling
- Missing and unique value statistics
- Numeric column statistics
- Data preview
- Uploaded file deletion
- Automated tests
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

Open:

- API documentation: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## Run tests

```powershell
python -m pytest
```

## Check code quality

```powershell
ruff check .
ruff format --check .
```