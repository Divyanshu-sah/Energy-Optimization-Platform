import io
from pathlib import Path

import pandas as pd


def dataframe_report(df: pd.DataFrame, name: str, sample_n: int = 5) -> str:
    buffer = io.StringIO()

    buffer.write("=" * 100 + "\n")
    buffer.write(f"DATASET: {name}\n")
    buffer.write("=" * 100 + "\n\n")

    buffer.write(f"Shape: {df.shape}\n")
    buffer.write(f"Columns ({len(df.columns)}):\n{list(df.columns)}\n\n")

    buffer.write("Dtypes:\n")
    buffer.write(df.dtypes.to_string())
    buffer.write("\n\n")

    buffer.write("Missing values per column:\n")
    buffer.write(df.isna().sum().to_string())
    buffer.write("\n\n")

    buffer.write("Head (first 5 rows):\n")
    buffer.write(df.head().to_string())
    buffer.write("\n\n")

    buffer.write(f"Random Sample ({min(sample_n, len(df))} rows):\n")
    if len(df) > 0:
        buffer.write(df.sample(min(sample_n, len(df)), random_state=42).to_string())
    else:
        buffer.write("Dataset is empty.")
    buffer.write("\n\n")

    buffer.write("Info:\n")
    info_buffer = io.StringIO()
    df.info(buf=info_buffer)
    buffer.write(info_buffer.getvalue())
    buffer.write("\n")

    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) > 0:
        buffer.write("Numeric Summary:\n")
        buffer.write(df[numeric_cols].describe().to_string())
        buffer.write("\n\n")

    object_cols = df.select_dtypes(include=["object", "category", "bool"]).columns
    if len(object_cols) > 0:
        buffer.write("Categorical/Object Summary:\n")
        try:
            buffer.write(df[object_cols].describe(include="all").to_string())
        except Exception as e:
            buffer.write(f"Could not generate categorical summary: {e}")
        buffer.write("\n\n")

    return buffer.getvalue()


def main() -> None:
    base_path = Path("synthetic")

    datasets = {
        "machine_metadata": pd.read_csv(base_path / "raw" / "machine_metadata.csv"),
        "telemetry_machine_level": pd.read_csv(
            base_path / "raw" / "telemetry_machine_level.csv"
        ),
        "anomalies_only": pd.read_csv(base_path / "processed" / "anomalies_only.csv"),
        "plant_demand_timeseries": pd.read_csv(
            base_path / "processed" / "plant_demand_timeseries.csv"
        ),
        "recommendations_reference": pd.read_csv(
            base_path / "processed" / "recommendations_reference.csv"
        ),
        "training_dataset_efficiency": pd.read_csv(
            base_path / "processed" / "training_dataset_efficiency.csv"
        ),
        "training_dataset_forecast": pd.read_csv(
            base_path / "processed" / "training_dataset_forecast.csv"
        ),
    }

    output_file = Path("dataset_report.txt")

    with output_file.open("w", encoding="utf-8") as f:
        for name, df in datasets.items():
            report = dataframe_report(df, name)
            f.write(report)
            f.write("\n\n")

    print(f"Dataset report saved to: {output_file.resolve()}")


if __name__ == "__main__":
    main()
