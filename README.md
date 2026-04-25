# 🧠 Chat With Your Dataset

An AI-powered data analysis web app where you upload any CSV and ask questions in plain English — getting back answers, charts, and insights instantly.

**Live Demo:** [chat-with-dataset-w3q3tiwx9b8duna8bdw9u6.streamlit.app](https://chat-with-dataset-w3q3tiwx9b8duna8bdw9u6.streamlit.app)

---

## What It Does

Upload a CSV file and ask natural language questions like:

- *"What are the top 5 products by revenue?"*
- *"Show sales trend over time"*
- *"Which region has the highest average order value?"*
- *"Is there a correlation between price and quantity?"*
- *"Why did revenue drop in Q3?"*

The app understands your question, generates Pandas code, executes it safely, visualizes the result, and explains the findings in plain English.

---

## Features

| Feature | Description |
|---|---|
| Natural Language Queries | Ask questions in plain English |
| AI Code Generation | Converts questions to Pandas code via Groq + Llama 3.3 70B |
| Auto-Visualization | Detects and renders the best chart type automatically |
| AI Explanations | Plain-English insights for every result |
| Follow-up Suggestions | 3 contextual next questions after each answer |
| Multi-Turn Conversation | Remembers context across follow-up questions |
| Dataset Summary | Auto-profiling on upload (types, nulls, stats) |
| Safe Code Execution | Sandboxed executor blocks dangerous operations |
| Download Results | Export any result as CSV |

---

## Tech Stack

- **Frontend:** Streamlit
- **AI / LLM:** Groq API · Llama 3.3 70B
- **Data Processing:** Pandas · NumPy
- **Visualization:** Plotly
- **Language:** Python 3.10+

---

## Project Structure

```
chat-with-dataset/
├── app.py              # Streamlit UI + main chat loop
├── data_loader.py      # CSV/Excel loading & dataset profiling
├── query_engine.py     # Natural language → Pandas code (via Groq)
├── executor.py         # Safe sandboxed code execution
├── visualization.py    # Auto chart detection & Plotly rendering
├── ai_explainer.py     # Result explanations & follow-up suggestions
├── conversation.py     # Multi-turn conversation history manager
├── utils.py            # Shared helper utilities
└── requirements.txt
```

---

## Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/Himaaanshu7/chat-with-dataset.git
cd chat-with-dataset
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your Groq API key
Get a free key at [console.groq.com](https://console.groq.com)

```bash
cp .env.example .env
# Edit .env and paste your key:
# GROQ_API_KEY=gsk_...
```

### 4. Run
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

---

## Architecture

```
User Question
      │
      ▼
 query_engine.py  ──► Groq API (Llama 3.3 70B)
      │                    │
      │            Generate Pandas code
      │                    │
      ▼                    ▼
 executor.py  ◄──── Validated & sandboxed
      │
      ├──► visualization.py  → Plotly chart
      │
      └──► ai_explainer.py ──► Groq API
                │                   │
                │           Plain-English explanation
                │           + Follow-up suggestions
                ▼
           Streamlit UI
```

---

## Example Queries

| Question | Result Type |
|---|---|
| Show top 10 customers by total spend | Table + Bar chart |
| What is the monthly revenue trend? | Line chart |
| Which product has the most returns? | Single value |
| Show distribution of customer ages | Histogram |
| Compare sales across regions | Bar chart |
| Is price correlated with quantity sold? | Scatter plot |

---

## Security

- Generated code is validated against a blocklist of dangerous keywords (`subprocess`, `os`, `socket`, `pickle`, etc.)
- Code executes in an isolated scope — no access to the filesystem or network
- Auto-correction retries up to 2 times on failure before showing a friendly error

---

## Deployment

Deployed on **Streamlit Community Cloud**.

To deploy your own instance:
1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Select your fork, branch `main`, file `app.py`
4. Add `GROQ_API_KEY` under Advanced Settings → Secrets
5. Deploy

---

## Author

**Himanshu Mishra**

---

## License

MIT
