import csv
from io import StringIO
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError
from pydantic import BaseModel

SUPPORTED_DELIMITERS = (",", ";")
ENCODING_CANDIDATES = (
    ("utf-8-sig", "UTF-8"),
    ("cp1251", "Windows-1251"),
)
SNIFF_SAMPLE_SIZE = 8192


class CsvReaderError(ValueError):
    pass


class EmptyCsvError(CsvReaderError):
    pass


class UnsupportedEncodingError(CsvReaderError):
    pass


class UnsupportedDelimiterError(CsvReaderError):
    pass


class InvalidCsvError(CsvReaderError):
    pass


class CsvFileInfo(BaseModel):
    encoding: str
    delimiter: str
    row_count: int
    column_count: int


class CsvReaderService:
    def inspect(self, file_path: Path) -> CsvFileInfo:
        raw_content = file_path.read_bytes()

        if not raw_content or not raw_content.strip():
            raise EmptyCsvError("The CSV file is empty.")

        text, encoding = self._decode(raw_content)

        if not text.strip():
            raise EmptyCsvError("The CSV file is empty.")

        delimiter = self._detect_delimiter(text)
        self._validate_rows(text, delimiter)

        try:
            dataframe = pd.read_csv(
                StringIO(text),
                sep=delimiter,
                dtype=str,
                keep_default_na=False,
                on_bad_lines="error",
            )
        except EmptyDataError as exc:
            raise EmptyCsvError("The CSV file is empty.") from exc
        except (ParserError, UnicodeError, ValueError) as exc:
            raise InvalidCsvError("The CSV file could not be parsed.") from exc

        if dataframe.columns.empty:
            raise InvalidCsvError("The CSV file does not contain columns.")

        return CsvFileInfo(
            encoding=encoding,
            delimiter=delimiter,
            row_count=len(dataframe.index),
            column_count=len(dataframe.columns),
        )

    @staticmethod
    def _decode(raw_content: bytes) -> tuple[str, str]:
        for python_encoding, display_name in ENCODING_CANDIDATES:
            try:
                text = raw_content.decode(python_encoding)
            except UnicodeDecodeError:
                continue

            if CsvReaderService._contains_binary_control_characters(text):
                raise UnsupportedEncodingError(
                    "The file must be a text CSV encoded as UTF-8 or Windows-1251."
                )

            return text, display_name

        raise UnsupportedEncodingError("The CSV file must be encoded as UTF-8 or Windows-1251.")

    @staticmethod
    def _contains_binary_control_characters(text: str) -> bool:
        allowed_control_characters = {"\n", "\r", "\t"}

        return any(
            ord(character) < 32 and character not in allowed_control_characters
            for character in text
        )

    @staticmethod
    def _detect_delimiter(text: str) -> str:
        sample = text[:SNIFF_SAMPLE_SIZE]

        try:
            dialect = csv.Sniffer().sniff(
                sample,
                delimiters="".join(SUPPORTED_DELIMITERS),
            )
            return dialect.delimiter
        except csv.Error:
            first_non_empty_line = next(
                (line for line in text.splitlines() if line.strip()),
                "",
            )

            delimiter_counts = {
                delimiter: first_non_empty_line.count(delimiter)
                for delimiter in SUPPORTED_DELIMITERS
            }

            delimiter = max(delimiter_counts, key=delimiter_counts.get)

            if delimiter_counts[delimiter] == 0:
                raise UnsupportedDelimiterError(
                    "The CSV file must use a comma or semicolon delimiter."
                ) from None

            return delimiter

    @staticmethod
    def _validate_rows(text: str, delimiter: str) -> None:
        try:
            rows = csv.reader(
                StringIO(text, newline=""),
                delimiter=delimiter,
                strict=True,
            )
            header = next(rows)
        except StopIteration as exc:
            raise EmptyCsvError("The CSV file is empty.") from exc
        except csv.Error as exc:
            raise InvalidCsvError("The CSV file could not be parsed.") from exc

        if len(header) < 2:
            raise UnsupportedDelimiterError("The CSV file must use a comma or semicolon delimiter.")

        if any(not column_name.strip() for column_name in header):
            raise InvalidCsvError("CSV column names must not be empty.")

        expected_column_count = len(header)

        try:
            for row in rows:
                if not row or all(not value.strip() for value in row):
                    continue

                if len(row) != expected_column_count:
                    raise InvalidCsvError("All CSV rows must contain the same number of columns.")
        except csv.Error as exc:
            raise InvalidCsvError("The CSV file could not be parsed.") from exc
