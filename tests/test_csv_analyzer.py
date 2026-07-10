from pathlib import Path

from app.services.csv_analyzer import CsvAnalyzerService


def test_analyze_calculates_numeric_statistics(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "sales.csv"
    file_path.write_text(
        "product,amount\nCoffee,10\nTea,20\nBread,\n",
        encoding="utf-8",
    )

    analysis = CsvAnalyzerService().analyze(
        file_path=file_path,
        encoding="UTF-8",
        delimiter=",",
    )

    amount = next(column for column in analysis.columns if column.name == "amount")

    assert amount.data_type == "number"
    assert amount.missing_values == 1
    assert amount.unique_values == 2
    assert amount.numeric_statistics is not None
    assert amount.numeric_statistics.minimum == 10.0
    assert amount.numeric_statistics.maximum == 20.0
    assert amount.numeric_statistics.average == 15.0
    assert amount.numeric_statistics.median == 15.0


def test_analyze_infers_text_boolean_datetime_and_empty(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "types.csv"
    file_path.write_text(
        ("name,active,created_at,comment\nAlice,true,2026-07-01,\nBob,false,2026-07-02,\n"),
        encoding="utf-8",
    )

    analysis = CsvAnalyzerService().analyze(
        file_path=file_path,
        encoding="UTF-8",
        delimiter=",",
    )

    types = {column.name: column.data_type for column in analysis.columns}

    assert types == {
        "name": "text",
        "active": "boolean",
        "created_at": "datetime",
        "comment": "empty",
    }
