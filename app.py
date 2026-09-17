"""
app.py: the web app for the Knowledge Assistant.

Run it:
    uv run app.py
Then open http://127.0.0.1:7860 (it opens automatically).
Stop it with Ctrl + C in the terminal.
"""

if __name__ == "__main__":
    print("Starting the app... (loading libraries)", flush=True)

import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")  # no usage stats sent to Gradio

import gradio as gr

import pandas as pd

import config
import evaluate
import rag

# Example questions shown under the chat (they match the sample knowledge base;
# change them when you use your own documents)
EXAMPLES = [
    "What is the maximum photo upload size?",
    "When is code freeze in release week?",
    "What are the quiet hours for push notifications?",
    "Which devices are Tier 1?",
]


# Status checks shown at the top of the page
def ollama_status():
    try:
        names = [m.id for m in rag.client.models.list().data]
    except Exception:
        return "🔴 Ollama not reachable: start the Ollama app"
    if not any(n == config.MODEL or n.startswith(config.MODEL + ":") for n in names):
        return f"🟠 Ollama is running, but `{config.MODEL}` is missing: run `ollama pull {config.MODEL}`"
    return f"🟢 Ollama connected · model `{config.MODEL}`"


def knowledge_status():
    count = rag.get_store()._collection.count()
    if count == 0:
        return "🔴 Vector database is empty: run `uv run ingest.py`"
    return f"🟢 {count} chunks in Chroma · top {config.TOP_K} retrieved per question"


# Chat
# Gradio builds the web UI. ChatInterface keeps the conversation history
# and passes it to our function on every message.
def chat(message, history):
    # rag.answer yields the reply so far, so the text streams into the chat
    yield from rag.answer(message, history)


# Evaluation tab
# Scores retrieval (MRR, nDCG, keyword coverage) and answers
# (LLM-as-a-judge) on a fixed set of test questions.
RESULT_COLUMNS = ["#", "category", "question", "mrr", "ndcg", "keyword_coverage",
                  "accuracy", "completeness", "relevance", "answer", "feedback"]


def for_display(table):
    """Same columns every time; long answers are shortened here (the CSV keeps them in full)."""
    table = table.reindex(columns=RESULT_COLUMNS)
    for column in ("answer", "feedback"):
        table[column] = table[column].fillna("").astype(str).map(
            lambda text: text if len(text) <= 160 else text[:157] + "...")
    return table


def summary_markdown(averages, title):
    lines = [f"#### {title}", "", "| Metric | Score | Rating |", "|---|---|---|"]
    for name, value in averages.items():
        if pd.isna(value):
            continue
        lines.append(f"| {name} | **{value:.3f}** | {evaluate.rating(name, value)} |")
    return "\n".join(lines)


def load_history():
    if evaluate.SUMMARY_FILE.exists():
        return pd.read_csv(evaluate.SUMMARY_FILE).iloc[::-1]  # newest run first
    return pd.DataFrame(columns=["time", "model", "k", "chunk_size", "judge", "MRR", "nDCG",
                                 "Keyword coverage (%)"])


def load_last_results():
    """Show the latest saved results when the page opens."""
    history = load_history()
    if history.empty or not config.EVAL_RESULTS_FILE.exists():
        return ("No evaluation yet. Press **Run evaluation**.",
                pd.DataFrame(columns=RESULT_COLUMNS), history)
    last = history.iloc[0]
    metrics = {c: last[c] for c in history.columns
               if c not in ("time", "model", "k", "chunk_size", "judge")}
    title = f"Last run: {last['time']} · k={last['k']} · chunk_size={last['chunk_size']}"
    table = pd.read_csv(config.EVAL_RESULTS_FILE)
    return summary_markdown(metrics, title), for_display(table), history


def run_evaluation_from_app(k, use_judge, progress=gr.Progress()):
    k = int(k)

    def report(i, total, question):
        progress((i - 1, total), desc=f"Question {i}/{total}: {question}")

    try:
        table, averages = evaluate.run_evaluation(k, use_judge, report)
    except Exception as error:
        raise gr.Error(rag.friendly_error(error))  # shows a pop-up instead of crashing
    evaluate.save_results(table, averages, k, config.CHUNK_SIZE, use_judge)
    title = f"This run: k={k} · chunk_size={config.CHUNK_SIZE} · judge={'on' if use_judge else 'off'}"
    return (summary_markdown(averages, title),
            for_display(table),
            load_history())


def build_evaluation_tab():
    gr.Markdown(
        f"Scores the assistant on **{len(evaluate.load_tests())} fixed test questions** "
        "(`evaluation/tests.jsonl`).\n\n"
        "| Check | What it measures |\n|---|---|\n"
        "| **Retrieval** | Did we fetch the right chunks? *MRR*: is the right chunk near the top? "
        "*nDCG*: are all relevant chunks ranked high? *Keyword coverage*: were the expected facts found? |\n"
        "| **Answers** | An *LLM-as-a-judge* scores accuracy, completeness and relevance from 1 to 5 |\n\n"
        "⏱️ With the judge on, this takes a few minutes on a laptop. "
        "Note: the judge is the same small local model, so it is less strict than a large model would be."
    )
    with gr.Row():
        k_slider = gr.Slider(1, 10, value=config.TOP_K, step=1, label="k (chunks retrieved per question)")
        judge_box = gr.Checkbox(value=True, label="Include LLM-as-a-judge (slower)")
        run_button = gr.Button("▶ Run evaluation", variant="primary")
    summary = gr.Markdown()
    results = gr.Dataframe(label="Results per question", wrap=True, max_height=420,
                           column_widths=["4%", "10%", "18%", "6%", "6%", "7%", "7%", "7%", "7%", "14%", "14%"])
    history = gr.Dataframe(label="Run history (compare settings, newest first)", max_height=260)

    run_button.click(run_evaluation_from_app, inputs=[k_slider, judge_box],
                     outputs=[summary, results, history])
    return summary, results, history


HOW_IT_WORKS = f"""
### How a question is answered

```
 Your question
      ▼
 1. Embed      all-MiniLM-L6-v2 turns it into 384 numbers
      ▼
 2. Retrieve   Chroma finds the {config.TOP_K} closest chunks
      ▼
 3. Augment    the chunks are added to the system prompt
      ▼
 4. Generate   {config.MODEL} (local, via Ollama) writes the answer
      ▼
 Answer + 📄 sources
```

### What's inside

| Part | File |
|---|---|
| Local LLM through the OpenAI client (Ollama) | `config.py`, `rag.py` |
| System prompt that forbids guessing | `rag.py` |
| Document loading with metadata (.md, .pdf, .docx, .txt) | `ingest.py` |
| Chunking with overlap ({config.CHUNK_SIZE} / {config.CHUNK_OVERLAP}) | `ingest.py` |
| Embeddings + Chroma vector database | `vector_store.py`, `ingest.py` |
| t-SNE vector map | `visualize.py` |
| Retrieval + prompt augmentation (RAG) | `rag.py` |
| Gradio chat UI with streaming | `app.py` |
| RAG evaluation: MRR, nDCG, LLM-as-a-judge | `evaluate.py` |
| Structured output with Pydantic (judge JSON) | `evaluate.py` |
"""


def build_app():
    with gr.Blocks(title="Knowledge Assistant") as demo:
        gr.Markdown(
            "# Knowledge Assistant\n"
            "Ask questions about the documents in the knowledge base (Markdown, PDF, Word and text files). "
            "Answers come **only** from those documents, and each one lists its sources."
        )
        with gr.Row():
            ollama_box = gr.Markdown("Checking Ollama...")
            knowledge_box = gr.Markdown("Checking the vector database...")

        with gr.Tab("💬 Chat"):
            gr.ChatInterface(
                fn=chat,
                chatbot=gr.Chatbot(
                    height=480,
                    placeholder="Ask a question about your documents.",
                ),
                examples=EXAMPLES,
                textbox=gr.Textbox(
                    placeholder="Type a question and press Enter",
                    submit_btn="Ask",
                    stop_btn=True,
                ),
            )

        with gr.Tab("📊 Evaluation"):
            eval_outputs = build_evaluation_tab()

        with gr.Tab("ℹ️ How it works"):
            gr.Markdown(HOW_IT_WORKS)

        # Re-check the status every time the page is opened or refreshed
        demo.load(lambda: (ollama_status(), knowledge_status()), outputs=[ollama_box, knowledge_box])
        demo.load(load_last_results, outputs=list(eval_outputs))

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        inbrowser=True,           # opens the browser for you
        theme=gr.themes.Soft(),
    )
