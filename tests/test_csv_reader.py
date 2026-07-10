from pathlib import Path

import pytest

from app.services.csv_reader import (
    CsvReaderService,
    InvalidCsvError,
    UnsupportedEncodingError,
)


def test_inspect_detects_utf8_and_comma(tmp_path: Path) -> None:
    file_path = tmp_path / "sales.csv"
    file_path.write_text(
        "name,amount\nCoffee,10\nTea,5\n",
        encoding="utf-8",
    )

    info = CsvReaderService().inspect(file_path)

    assert info.encoding == "UTF-8"
    assert info.delimiter == ","
    assert info.row_count == 2
    assert info.column_count == 2


def test_inspect_detects_windows_1251_and_semicolon(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "products.csv"
    file_path.write_bytes("name;city\nКофе;Минск\n".encode("cp1251"))

    info = CsvReaderService().inspect(file_path)

    assert info.encoding == "Windows-1251"
    assert info.delimiter == ";"
    assert info.row_count == 1
    assert info.column_count == 2


def test_inspect_rejects_binary_control_characters(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "binary.csv"
    file_path.write_bytes(b"name,amount\x00\nCoffee,10\n")

    with pytest.raises(UnsupportedEncodingError):
        CsvReaderService().inspect(file_path)


def test_inspect_rejects_unclosed_quoted_field(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "broken.csv"
    file_path.write_text(
        'name,amount\n"Coffee,10\n',
        encoding="utf-8",
    )

    with pytest.raises(InvalidCsvError):
        CsvReaderService().inspect(file_path)
