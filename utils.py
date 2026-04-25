from typing import Any

import numpy as np
import pandas as pd


def result_to_download_csv(result: Any) -> str:
    """Convert a result to a CSV string for the download button."""
    if isinstance(result, pd.DataFrame):
        return result.to_csv(index=False)
    if isinstance(result, pd.Series):
        return result.reset_index().to_csv(index=False)
    # Scalar / list / dict → wrap in a single-column CSV
    return pd.DataFrame({"result": [result]}).to_csv(index=False)


def is_visualisable(result: Any) -> bool:
    """Return True if the result can meaningfully be plotted."""
    if isinstance(result, pd.DataFrame):
        return result.select_dtypes(include=np.number).shape[1] >= 1
    if isinstance(result, pd.Series):
        return True
    return False


def friendly_dtype(dtype_str: str) -> str:
    """Map a pandas dtype string to a user-friendly label."""
    dtype_str = dtype_str.lower()
    if "int" in dtype_str:
        return "Integer"
    if "float" in dtype_str:
        return "Decimal"
    if "datetime" in dtype_str:
        return "Date/Time"
    if "bool" in dtype_str:
        return "Boolean"
    if "object" in dtype_str or "string" in dtype_str:
        return "Text"
    if "category" in dtype_str:
        return "Category"
    return dtype_str.capitalize()


def format_number(value: Any) -> str:
    """Format a numeric value with commas and up to 4 significant figures."""
    try:
        f = float(value)
        if f == int(f):
            return f"{int(f):,}"
        return f"{f:,.4g}"
    except (TypeError, ValueError):
        return str(value)
