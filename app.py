"""
Chat With Your Dataset
======================
Upload a CSV, ask questions in plain English, get answers + charts + insights.
Powered by Groq (free) + Llama 3.3 70B.
"""

import os
from typing import Any

from groq import Groq
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from ai_explainer import generate_explanation, generate_followup_questions
from conversation import ConversationManager
from data_loader import get_dataset_summary, load_dataset, format_summary_for_prompt
from executor import execute_code, result_to_summary
from query_engine import generate_pandas_code
from utils import friendly_dtype, is_visualisable, result_to_download_csv
from visualization import create_chart

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Chat With Your Dataset",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_dotenv()

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def _init_state() -> None:
    defaults = {
        "df": None,
        "filename": "",
        "conversation": ConversationManager(),
        "messages": [],
        "api_key": os.getenv("GROQ_API_KEY", ""),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


def _get_client() -> Groq:
    key = st.session_state.api_key
    if not key:
        st.error(
            "No Groq API key found. Add `GROQ_API_KEY=...` to your `.env` file "
            "or paste it in the sidebar. Get a free key at https://console.groq.com"
        )
        st.stop()
    return Groq(api_key=key)


def _display_result(result: Any) -> None:
    if isinstance(result, pd.DataFrame):
        st.dataframe(result, use_container_width=True,
                     height=min(300, 35 * len(result) + 40))
    elif isinstance(result, pd.Series):
        st.dataframe(result.reset_index(), use_container_width=True,
                     height=min(300, 35 * len(result) + 40))
    elif result is not None:
        st.metric(label="Result", value=str(result))


def _run_query(question: str) -> None:
    df: pd.DataFrame = st.session_state.df
    client = _get_client()
    conversation: ConversationManager = st.session_state.conversation
    df_summary = format_summary_for_prompt(df)

    conversation.add_user(question)
    st.session_state.messages.append({"role": "user", "content": question})

    with st.spinner("Analyzing…"):
        # 1. Generate code
        ctx = conversation.get_context_summary()
        code, code_err = generate_pandas_code(question, df, client, ctx)

        if code_err or not code:
            err_msg = code_err or "Model returned empty code."
            conversation.add_assistant(err_msg, had_error=True)
            st.session_state.messages.append({
                "role": "assistant", "content": err_msg,
                "code": None, "result": None, "fig": None, "followups": [],
            })
            return

        # 2. Execute
        result, stdout, exec_err = execute_code(code, df)

        # 3. Auto-fix on error (up to 2 attempts)
        attempts = 0
        while exec_err and attempts < 2:
            attempts += 1
            fix_prompt = (
                f"This Python/Pandas code raised an error:\n\n{code}\n\n"
                f"Error: {exec_err}\n\n"
                f"Dataset columns: {list(df.columns)}\n"
                f"Sample data:\n{df.head(2).to_string()}\n\n"
                f"Write a SIMPLE corrected version. Store result in `result`. "
                f"No imports. No markdown. Only Python code."
            )
            try:
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": fix_prompt}],
                )
                import re as _re
                fixed = _re.sub(r"```(?:python)?\n?|```", "", resp.choices[0].message.content).strip()
                result, stdout, exec_err = execute_code(fixed, df)
                if not exec_err:
                    code = fixed
            except Exception:
                break

        if exec_err:
            msg = (
                "I couldn't produce a working analysis for that question. "
                f"**Error:** `{exec_err}`\n\n"
                "Try rephrasing, or ask a simpler version of the question."
            )
            conversation.add_assistant(msg, code=code, had_error=True)
            st.session_state.messages.append({
                "role": "assistant", "content": msg,
                "code": code, "result": None, "fig": None, "followups": [],
            })
            return

        # 4. Visualise
        fig = create_chart(result, question) if is_visualisable(result) else None

        # 5. Explain
        explanation = generate_explanation(question, code, result, client, df_summary)

        # 6. Follow-ups
        followups = generate_followup_questions(question, result, df, client)

        conversation.add_assistant(explanation, code=code,
                                   result_summary=result_to_summary(result))
        st.session_state.messages.append({
            "role": "assistant",
            "content": explanation,
            "code": code,
            "result": result,
            "fig": fig,
            "followups": followups,
        })


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🧠 Chat With Your Dataset")
    st.caption("Created by Himanshu Mishra")

    if not st.session_state.api_key:
        key_input = st.text_input("Groq API Key", type="password",
                                   placeholder="gsk_…")
        if key_input:
            st.session_state.api_key = key_input
            st.rerun()

    st.divider()

    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    if uploaded and uploaded.name != st.session_state.filename:
        try:
            with st.spinner("Loading…"):
                df = load_dataset(uploaded)
            st.session_state.df = df
            st.session_state.filename = uploaded.name
            st.session_state.conversation.clear()
            st.session_state.messages = []
            st.success(f"Loaded **{uploaded.name}**")
        except Exception as exc:
            st.error(f"Failed to load: {exc}")

    if st.session_state.df is not None:
        df = st.session_state.df
        summary = get_dataset_summary(df)

        st.subheader("Dataset Overview")
        c1, c2 = st.columns(2)
        c1.metric("Rows", f"{summary['shape'][0]:,}")
        c2.metric("Columns", summary["shape"][1])
        c3, c4 = st.columns(2)
        c3.metric("Null cells", f"{sum(summary['null_counts'].values()):,}")
        c4.metric("Duplicate rows", f"{summary['duplicate_rows']:,}")

        with st.expander("Column details"):
            st.dataframe(pd.DataFrame({
                "Column": summary["columns"],
                "Type": [friendly_dtype(summary["dtypes"][c]) for c in summary["columns"]],
                "% Null": [f"{summary['null_pct'][c]:.1f}%" for c in summary["columns"]],
            }), use_container_width=True, hide_index=True)

        with st.expander("Sample data"):
            st.dataframe(df.head(5), use_container_width=True)

        if summary["numeric_cols"]:
            with st.expander("Numeric statistics"):
                st.dataframe(
                    df[summary["numeric_cols"]].describe().T.round(2),
                    use_container_width=True,
                )

        st.divider()
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.conversation.clear()
            st.session_state.messages = []
            st.rerun()

# ---------------------------------------------------------------------------
# Main area — empty state
# ---------------------------------------------------------------------------
if st.session_state.df is None:
    st.markdown(
        "<div style='text-align:center;padding:4rem 2rem'>"
        "<h1>🧠 Chat With Your Dataset</h1>"
        "<p style='font-size:1.2rem;color:#888'>Upload a CSV or Excel file in the sidebar, "
        "then ask anything in plain English.</p></div>",
        unsafe_allow_html=True,
    )
    st.info("👈 Upload a dataset in the sidebar to get started.")
    st.subheader("Example questions:")
    for ex in [
        "What are the top 5 products by revenue?",
        "Show sales trend over time.",
        "Which region has the highest average order value?",
        "Is there a correlation between price and quantity?",
        "Show the distribution of customer ages.",
        "Why did revenue drop in Q3?",
    ]:
        st.markdown(f"- *{ex}*")
    st.stop()

# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------
st.markdown("### 💬 Conversation")

for msg_idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

            result = msg.get("result")
            fig    = msg.get("fig")
            code   = msg.get("code")
            followups = msg.get("followups", [])

            if fig is not None:
                st.plotly_chart(fig, use_container_width=True, key=f"fig_{msg_idx}")

            if result is not None or code:
                tab_labels = (
                    (["📊 Data"] if result is not None else [])
                    + (["🔍 Code"] if code else [])
                    + (["⬇️ Download"] if result is not None else [])
                )
                tabs = st.tabs(tab_labels)
                t = 0
                if result is not None:
                    with tabs[t]:
                        _display_result(result)
                    t += 1
                if code:
                    with tabs[t]:
                        st.code(code, language="python")
                    t += 1
                if result is not None:
                    with tabs[t]:
                        st.download_button(
                            "Download as CSV",
                            data=result_to_download_csv(result).encode(),
                            file_name=f"result_{msg_idx}.csv",
                            mime="text/csv",
                            key=f"dl_{msg_idx}",
                        )

            if followups:
                st.markdown("**Suggested follow-ups:**")
                cols = st.columns(len(followups))
                for i, fq in enumerate(followups):
                    if cols[i].button(fq, key=f"fq_{msg_idx}_{i}"):
                        _run_query(fq)
                        st.rerun()

# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------
prompt = st.chat_input("Ask a question about your dataset…")
if prompt:
    _run_query(prompt)
    st.rerun()
