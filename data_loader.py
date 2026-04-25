from typing import Any, Dict

import numpy as np
import pandas as pd


def load_dataset(uploaded_file) -> pd.DataFrame:
    """Load a CSV or Excel file uploaded via Streamlit into a DataFrame."""
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError(f"Unsupported format: '{name}'. Please upload a CSV or Excel file.")

    # Auto-parse columns that look like dates
    for col in df.select_dtypes(include="object").columns:
        try:
            parsed = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            if parsed.notna().mean() >= 0.8:
                df[col] = parsed
        except Exception:
            pass

    return df


def get_dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Return a structured summary dict for the uploaded dataset."""
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    dt_cols = df.select_dtypes(include="datetime64").columns.tolist()

    summary: Dict[str, Any] = {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "null_counts": df.isnull().sum().to_dict(),
        "null_pct": (df.isnull().mean() * 100).round(2).to_dict(),
        "numeric_cols": numeric_cols,
        "categorical_cols": cat_cols,
        "datetime_cols": dt_cols,
        "duplicate_rows": int(df.duplicated().sum()),
    }

    if numeric_cols:
        summary["numeric_stats"] = df[numeric_cols].describe().to_dict()

    # Top-5 value counts for up to 6 categorical columns
    summary["cat_preview"] = {
        col: df[col].value_counts().head(5).to_dict()
        for col in cat_cols[:6]
    }

    return summary


def format_summary_for_prompt(df: pd.DataFrame) -> str:
    """Return a compact plain-text description of the dataset for Claude prompts."""
    s = get_dataset_summary(df)
    rows, cols = s["shape"]
    lines = [f"Dataset: {rows:,} rows × {cols} columns"]

    lines.append("\nColumns (name | type | % null):")
    for col in s["columns"]:
        dtype = s["dtypes"][col]
        null_pct = s["null_pct"][col]
        null_tag = f" | {null_pct}% null" if null_pct > 0 else ""
        lines.append(f"  • {col}  ({dtype}){null_tag}")

    if s["numeric_cols"]:
        lines.append(f"\nNumeric  : {', '.join(s['numeric_cols'])}")
    if s["categorical_cols"]:
        lines.append(f"Category : {', '.join(s['categorical_cols'])}")
    if s["datetime_cols"]:
        lines.append(f"Datetime : {', '.join(s['datetime_cols'])}")

    return "\n".join(lines)
