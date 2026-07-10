from pathlib import Path

import pandas as pd
from pandas import Series
from pydantic import BaseModel

ENCODING_MAP = {
    "UTF-8": "utf-8-sig",
    "Windows-1251": "cp1251",
}
BOOLEAN_VALUES = {"true", "false", "yes", "no"}


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


class CsvAnalyzerService:
    def analyze(
        self,
        file_path: Path,
        encoding: str,
        delimiter: str,
    ) -> CsvAnalysis:
        dataframe = pd.read_csv(
            file_path,
            sep=delimiter,
            encoding=ENCODING_MAP[encoding],
            dtype=str,
            keep_default_na=False,
            on_bad_lines="error",
        )

        columns = [
            self._analyze_column(column_name, dataframe[column_name])
            for column_name in dataframe.columns
        ]

        return CsvAnalysis(columns=columns)

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

        numeric_values = pd.to_numeric(non_empty, errors="coerce")
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
