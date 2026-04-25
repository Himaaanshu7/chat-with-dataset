import re
from typing import Tuple

from groq import Groq
import pandas as pd

from data_loader import format_summary_for_prompt

MODEL = "llama-3.3-70b-versatile"


def _build_code_prompt(question: str, df: pd.DataFrame, context: str) -> str:
    dataset_info = format_summary_for_prompt(df)
    sample = df.head(3).to_string()
    ctx_block = f"\nPrevious conversation context:\n{context}\n" if context else ""

    return f"""You are an expert Python/Pandas data analyst. Write simple, correct Pandas code.

Dataset Information:
{dataset_info}

Sample rows (first 3):
{sample}
{ctx_block}
User question: {question}

Rules (follow strictly):
1. `df`, `pd`, and `np` are pre-loaded. Do NOT write any import statements.
2. Store the final answer in a variable called `result`.
3. Keep code SHORT and SIMPLE — avoid multi-step merges unless truly necessary.
4. For "top N by column" → use: result = df.nlargest(N, 'col')[['col1','col2']]
5. For groupby → use: result = df.groupby('col')['num_col'].sum().sort_values(ascending=False)
6. For filtering → use: result = df[df['col'] == value]
7. For counts → use: result = df['col'].value_counts().head(10)
8. Do NOT use set_index() unless the question specifically asks for it.
9. Do NOT wrap code in markdown fences or add any explanation.
10. If a column name has spaces, use df['column name'] syntax.

Return ONLY the Python code."""


def _extract_code(text: str) -> str:
    text = re.sub(r"```(?:python)?\n?", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


def generate_pandas_code(
    question: str,
    df: pd.DataFrame,
    client: Groq,
    conversation_context: str = "",
    model: str = MODEL,
) -> Tuple[str, str]:
    prompt = _build_code_prompt(question, df, conversation_context)
    try:
        resp = client.chat.completions.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        code = _extract_code(resp.choices[0].message.content)
        return code, ""
    except Exception as exc:
        return "", f"Groq API error: {exc}"
