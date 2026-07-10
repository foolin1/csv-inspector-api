from pathlib import Path

import pandas as pd
from pandas import DataFrame, Series
from pydantic import BaseModel

ENCODING_MAP = {
    "UTF-8": "utf-8-sig",
    "Windows-1251": "cp1251",
}
BOOLEAN_VALUES = {"true", "false", "yes", "no"}

type PreviewRow = dict[str, str | None]


class ColumnNotFoundError(ValueError):
    pass


class NumericStatistics(BaseModel):
    minimum: float
    maximum: float
    average: float
    median: float


class ColumnAnalysis(BaseModel):
    name: str
    data_type: str
    missing_values: int
    unique_values: int
    numeric_statistics: NumericStatistics | None = None


class CsvAnalysis(BaseModel):
    columns: list[ColumnAnalysis]


class CsvPreview(BaseModel):
    columns: list[str]
    rows: list[PreviewRow]


class CsvAnalyzerService:
    def analyze(
        self,
        file_path: Path,
        encoding: str,
        delimiter: str,
    ) -> CsvAnalysis:
        dataframe = self._read_dataframe(file_path, encoding, delimiter)

        columns = [
            self._analyze_column(str(column_name), dataframe[column_name])
            for column_name in dataframe.columns
        ]

        return CsvAnalysis(columns=columns)

    def preview(
        self,
        file_path: Path,
        encoding: str,
        delimiter: str,
        row_limit: int,
    ) -> CsvPreview:
        dataframe = self._read_dataframe(file_path, encoding, delimiter)
        preview_dataframe = dataframe.head(row_limit)

        rows = [
            {
                str(column_name): self._normalize_preview_value(value)
                for column_name, value in record.items()
            }
            for record in preview_dataframe.to_dict(orient="records")
        ]

        return CsvPreview(
            columns=[str(column_name) for column_name in dataframe.columns],
            rows=rows,
        )

    def analyze_column(
        self,
        file_path: Path,
        encoding: str,
        delimiter: str,
        column_name: str,
    ) -> ColumnAnalysis:
        dataframe = self._read_dataframe(file_path, encoding, delimiter)

        if column_name not in dataframe.columns:
            raise ColumnNotFoundError(f'The column "{column_name}" was not found.')

        return self._analyze_column(
            column_name,
            dataframe[column_name],
        )

    @staticmethod
    def _read_dataframe(
        file_path: Path,
        encoding: str,
        delimiter: str,
    ) -> DataFrame:
        return pd.read_csv(
            file_path,
            sep=delimiter,
            encoding=ENCODING_MAP[encoding],
            dtype=str,
            keep_default_na=False,
            on_bad_lines="error",
        )

    def _analyze_column(
        self,
        column_name: str,
        series: Series,
    ) -> ColumnAnalysis:
        normalized = series.astype(str).str.strip()
        non_empty = normalized[normalized != ""]

        missing_values = int(len(normalized) - len(non_empty))
        unique_values = int(non_empty.nunique())
        data_type, numeric_statistics = self._infer_data_type(non_empty)

        return ColumnAnalysis(
            name=str(column_name),
            data_type=data_type,
            missing_values=missing_values,
            unique_values=unique_values,
            numeric_statistics=numeric_statistics,
        )

    @staticmethod
    def _infer_data_type(
        non_empty: Series,
    ) -> tuple[str, NumericStatistics | None]:
        if non_empty.empty:
            return "empty", None

        numeric_values = pd.to_numeric(
            non_empty,
            errors="coerce",
        )

        if numeric_values.notna().all():
            return "number", NumericStatistics(
                minimum=float(numeric_values.min()),
                maximum=float(numeric_values.max()),
                average=float(numeric_values.mean()),
                median=float(numeric_values.median()),
            )

        lowercase_values = non_empty.str.casefold()

        if lowercase_values.isin(BOOLEAN_VALUES).all():
            return "boolean", None

        datetime_values = pd.to_datetime(
            non_empty,
            errors="coerce",
            format="mixed",
        )

        if datetime_values.notna().all():
            return "datetime", None

        return "text", None

    @staticmethod
    def _normalize_preview_value(
        value: object,
    ) -> str | None:
        text = str(value)

        return None if not text.strip() else text
