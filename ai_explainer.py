import json
from typing import Any, List

from groq import Groq
import numpy as np
import pandas as pd

from executor import result_to_summary

MODEL = "llama-3.3-70b-versatile"


def _format_result(result: Any) -> str:
    if result is None:
        return "No result was produced."
    if isinstance(result, pd.DataFrame):
        sample = result.head(10).to_string() if len(result) > 10 else result.to_string()
        tail = f"\n…and {len(result) - 10:,} more rows." if len(result) > 10 else ""
        return f"DataFrame ({result.shape[0]:,} rows × {result.shape[1]} cols):\n{sample}{tail}"
    if isinstance(result, pd.Series):
        sample = result.head(10).to_string() if len(result) > 10 else result.to_string()
        tail = f"\n…and {len(result) - 10:,} more values." if len(result) > 10 else ""
        return f"Series ({len(result):,} values):\n{sample}{tail}"
    if isinstance(result, (int, float, np.integer, np.floating)):
        return f"Value: {result:,.4g}"
    return str(result)[:600]


def generate_explanation(
    question: str,
    code: str,
    result: Any,
    client: Groq,
    df_summary: str,
    model: str = MODEL,
) -> str:
    prompt = f"""You are a data analyst explaining findings to a non-technical business user.

Dataset context:
{df_summary}

User's question: "{question}"

Python/Pandas code used:
{code}

Result:
{_format_result(result)}

Write a clear, insightful explanation that:
1. Directly answers the question in the first sentence.
2. Highlights 2-3 key findings or patterns.
3. Notes any outliers, anomalies, or surprising values.
4. Uses plain English — no jargon, no raw code.
5. Is 3-5 sentences total.

Do NOT just restate the raw numbers — interpret and explain what they mean."""

    try:
        resp = client.chat.completions.create(
            model=model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        return f"(Could not generate explanation: {exc})"


def generate_followup_questions(
    question: str,
    result: Any,
    df: pd.DataFrame,
    client: Groq,
    model: str = MODEL,
) -> List[str]:
    columns_preview = ", ".join(df.columns[:12].tolist())
    result_summary = result_to_summary(result)

    prompt = f"""A user just asked: "{question}"
The analysis returned: {result_summary}
Available dataset columns: {columns_preview}

Suggest exactly 3 natural follow-up questions. They should:
- Progress logically from the current result
- Be specific and answerable with this dataset
- Vary: one simple, one comparative, one deeper insight

Return ONLY a JSON array of 3 strings:
["Question 1?", "Question 2?", "Question 3?"]"""

    try:
        resp = client.chat.completions.create(
            model=model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(resp.choices[0].message.content.strip())[:3]
    except Exception:
        return []
