import io
import re
import sys
import traceback
from typing import Any, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Safety — block dangerous keywords before execution
# ---------------------------------------------------------------------------
_BLOCKED = re.compile(
    r"\b(subprocess|shutil|socket|urllib|requests|"
    r"__import__|importlib|pickle)\b"
    r"|import\s+(os|sys|subprocess|shutil|socket)",
    re.IGNORECASE,
)


def validate_code(code: str) -> Tuple[bool, str]:
    match = _BLOCKED.search(code)
    if match:
        return False, f"Blocked keyword: '{match.group()}'"
    return True, ""


def execute_code(code: str, df: pd.DataFrame) -> Tuple[Any, str, str]:
    """
    Execute AI-generated Pandas code in a controlled sandbox.

    Returns
    -------
    (result, stdout_output, error_message)
    """
    ok, reason = validate_code(code)
    if not ok:
        return None, "", f"Safety check failed: {reason}"

    # Capture print() output
    old_stdout = sys.stdout
    sys.stdout = buf = io.StringIO()

    # Use full builtins so pandas internals work correctly;
    # the regex above already blocks dangerous patterns.
    globs: dict = {
        "__builtins__": __builtins__,
        "pd": pd,
        "pandas": pd,
        "np": np,
        "numpy": np,
        "df": df.copy(),
    }
    locs: dict = {}
    result = None
    error = ""

    try:
        exec(compile(code, "<generated>", "exec"), globs, locs)  # noqa: S102

        # Prefer explicit `result`; otherwise grab the last meaningful value
        if "result" in locs:
            result = locs["result"]
        else:
            for val in reversed(list(locs.values())):
                if isinstance(val, (pd.DataFrame, pd.Series, int, float,
                                    np.integer, np.floating, str, list, dict)):
                    result = val
                    break

        output = buf.getvalue()

    except Exception:
        tb = traceback.format_exc()
        # Extract just the last meaningful error line for display
        lines = [l for l in tb.strip().splitlines() if l.strip()]
        error = lines[-1] if lines else "Unknown error"
        output = buf.getvalue()
    finally:
        sys.stdout = old_stdout

    return result, output, error


def result_to_summary(result: Any) -> str:
    if result is None:
        return "No result produced."
    if isinstance(result, pd.DataFrame):
        return (
            f"DataFrame – {result.shape[0]:,} rows × {result.shape[1]} cols; "
            f"columns: {list(result.columns)}"
        )
    if isinstance(result, pd.Series):
        return f"Series – {len(result):,} values; name: {result.name}"
    if isinstance(result, (int, float, np.integer, np.floating)):
        return f"Value: {result:,.4g}"
    return str(result)[:300]
