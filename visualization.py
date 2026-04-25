from typing import Any, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def detect_chart_type(result: Any, question: str) -> Optional[str]:
    """Infer the most appropriate chart type from the result and question text."""
    q = question.lower()

    if any(w in q for w in ["trend", "over time", "time series", "monthly", "daily",
                              "weekly", "yearly", "annual", "growth", "progress"]):
        return "line"
    if any(w in q for w in ["distribution", "histogram", "spread", "frequency"]):
        return "histogram"
    if any(w in q for w in ["correlation", "scatter", "relationship", "vs", "versus"]):
        return "scatter"
    if any(w in q for w in ["proportion", "share", "pie", "breakdown", "composition"]):
        return "pie"
    if any(w in q for w in ["top", "bottom", "rank", "highest", "lowest",
                              "compare", "comparison", "by category", "per"]):
        return "bar"

    # Fall back to result shape
    if isinstance(result, pd.Series):
        return "line" if pd.api.types.is_datetime64_any_dtype(result.index) else "bar"

    if isinstance(result, pd.DataFrame):
        dt_cols = result.select_dtypes(include="datetime64").columns
        num_cols = result.select_dtypes(include=np.number).columns
        if len(dt_cols) and len(num_cols):
            return "line"
        if len(num_cols) >= 2 and len(result) > 30:
            return "scatter"
        if len(num_cols):
            return "bar"

    return None


def create_chart(result: Any, question: str,
                 chart_type: Optional[str] = None) -> Optional[go.Figure]:
    """Build a Plotly figure from the analysis result."""
    if result is None:
        return None

    if chart_type is None:
        chart_type = detect_chart_type(result, question)
    if chart_type is None:
        return None

    try:
        if isinstance(result, pd.Series):
            return _series_chart(result, chart_type, question)
        if isinstance(result, pd.DataFrame):
            return _dataframe_chart(result, chart_type, question)
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_LAYOUT = dict(template="plotly_white", title_font_size=15, margin=dict(t=50, l=10, r=10, b=10))


def _series_chart(series: pd.Series, chart_type: str, title: str) -> go.Figure:
    df = series.reset_index()
    df.columns = ["x", "y"]

    if chart_type == "line":
        fig = px.line(df, x="x", y="y", title=title, markers=True)
    elif chart_type == "pie":
        fig = px.pie(df, names="x", values="y", title=title)
    elif chart_type == "histogram":
        fig = px.histogram(x=series.values, title=title, nbins=30)
    else:  # bar (default)
        fig = px.bar(df, x="x", y="y", title=title,
                     color="y", color_continuous_scale="Blues")
        fig.update_coloraxes(showscale=False)

    fig.update_layout(**_LAYOUT)
    return fig


def _dataframe_chart(df: pd.DataFrame, chart_type: str, title: str) -> Optional[go.Figure]:
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    dt_cols = df.select_dtypes(include="datetime64").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not num_cols:
        return None

    y_col = num_cols[0]

    # Choose x axis
    if dt_cols:
        x_col = dt_cols[0]
    elif cat_cols:
        x_col = cat_cols[0]
    elif len(num_cols) >= 2:
        x_col, y_col = num_cols[0], num_cols[1]
    else:
        x_col = df.index

    if chart_type == "line":
        extra_y = num_cols[1:4] if len(num_cols) > 1 else []
        y_axis = [y_col] + extra_y if extra_y else y_col
        fig = px.line(df, x=x_col, y=y_axis, title=title, markers=True)

    elif chart_type == "bar":
        color_col = cat_cols[1] if len(cat_cols) > 1 else None
        fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title,
                     barmode="group" if color_col else "relative")

    elif chart_type == "scatter":
        x_s = num_cols[0] if len(num_cols) >= 2 else x_col
        y_s = num_cols[1] if len(num_cols) >= 2 else y_col
        color_col = cat_cols[0] if cat_cols else None
        fig = px.scatter(df, x=x_s, y=y_s, color=color_col, title=title,
                         trendline="ols" if len(df) > 5 else None)

    elif chart_type == "histogram":
        fig = px.histogram(df, x=y_col, title=title, nbins=30)

    elif chart_type == "pie":
        if cat_cols:
            fig = px.pie(df, names=cat_cols[0], values=y_col, title=title)
        else:
            return None
    else:
        fig = px.bar(df, x=x_col, y=y_col, title=title)

    fig.update_layout(**_LAYOUT)
    return fig
