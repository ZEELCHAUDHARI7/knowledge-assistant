# Knowledge Assistant

A chatbot that answers questions about your own documents (**Markdown, PDF, Word and text files**) **using only those documents**. Every answer lists its sources, the assistant says "I don't know" when the answer isn't in the documents, and it can score its own quality. Everything runs **free and locally** with Ollama.

> `knowledge_base/` contains a small example set of documents for a made-up mobile app team, so you can try the assistant straight away. All names, URLs and numbers in it are fictional. Replace it with your own files (see **Use your own documents**).

## Features

| Feature | Details |
|---|---|
| Answers from your own files | Reads `.md`, `.pdf`, `.docx` and `.txt` files |
| Sources on every answer | For example `release-checklist.md` or `notifications-module.pdf (p. 1)` |
| No guessing | Says it doesn't know when the documents don't cover the question |
| Follow-up questions | Remembers the conversation ("and what about iOS?") |
| Vector map | Interactive t-SNE chart of all chunks, coloured by folder |
| Built-in evaluation | Retrieval scores (MRR, nDCG, keyword coverage) and answer scores (LLM-as-a-judge) |
| Run history | Compare settings such as 2 vs 5 retrieved chunks |
| Web app | Chat, Evaluation and How it works tabs |
| Local and free | Ollama (Llama 3.2), HuggingFace embeddings, Chroma, Gradio |

## Tech stack

| Part | Used for | File |
|---|---|---|
| Ollama + Llama 3.2 (through the OpenAI Python client) | Writing answers, judging answers | `config.py`, `rag.py` |
| pypdf, python-docx | Reading PDF and Word files | `ingest.py` |
| LangChain `RecursiveCharacterTextSplitter` | Chunking (1000 characters, 200 overlap) | `ingest.py` |
| HuggingFace `all-MiniLM-L6-v2` | Embeddings (384 dimensions) | `vector_store.py` |
| Chroma | Vector database | `vector_store.py`, `ingest.py` |
| scikit-learn t-SNE + Plotly | Vector map | `visualize.py` |
| Gradio | Web app with streaming answers | `app.py` |
| Pydantic | Structured JSON from the judge | `evaluate.py` |

## How it works

```
                    ┌──────────────── ingest.py (run once) ────────────────┐
 knowledge_base/ ──►│ 13 files → 36 chunks → 36 vectors (384 numbers)      │──► vector_db/ (Chroma)
                    └──────────────────────────────────────────────────────┘
                                                                                  │
 Your question ──► 1. Embed the question                                          │
                   2. Retrieve the 5 closest chunks  ◄────────────────────────────┘
                   3. Augment: put the chunks in the system prompt
                   4. Generate: llama3.2 (Ollama) writes the answer
                                  │
                                  ▼
                   Answer + 📄 Sources checked          (rag.py, app.py)

 evaluate.py: 12 test questions → retrieval scores (MRR, nDCG, coverage)
                                → answer scores (LLM-as-a-judge, 1 to 5)
```

## Project files

```
knowledge-assistant/
├── config.py               all settings (model, chunk size, top k, paths)
├── knowledge_base/         example documents (.md, .pdf, .docx, .txt) in 5 folders
├── vector_store.py         embedding model + Chroma connection
├── ingest.py               files → chunks → vectors → Chroma
├── visualize.py            t-SNE vector map → vector_map.html
├── rag.py                  retrieve + prompt + answer (also a terminal chat)
├── app.py                  Gradio web app
├── evaluation/tests.jsonl  12 test questions with keywords and reference answers
├── evaluate.py             scores → eval_results.csv + eval_summary.csv
└── pyproject.toml, uv.lock exact package versions
```

The scripts create `vector_db/`, `vector_map.html`, `eval_results.csv` and `eval_summary.csv` when they run.

## Setup

1. **Install Ollama** from https://ollama.com, then run:
   ```
   ollama pull llama3.2
   ```
2. **Install uv.** On Windows (PowerShell):
   ```
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   On macOS or Linux:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Get the code and install the packages:**
   ```
   git clone https://github.com/ZEELCHAUDHARI7/knowledge-assistant.git
   cd knowledge-assistant
   uv sync
   ```
   The first install downloads about 1 GB (mostly PyTorch).

## Usage

Make sure the **Ollama app is running**, then:

| # | Command | Result |
|---|---|---|
| 1 | `uv run ingest.py` | Builds `vector_db/` (13 files → about 36 chunks, 384 dimensions) |
| 2 | `uv run visualize.py` | Opens the vector map (add `--3d` for a map you can rotate) |
| 3 | `uv run rag.py "What is the maximum photo upload size?"` | One answer in the terminal (add `--show-chunks` to see what was retrieved) |
| 4 | `uv run app.py` | Web app at http://127.0.0.1:7860 (stop it with **Ctrl + C**) |
| 5 | `uv run evaluate.py` | Full scorecard (takes a few minutes) |

Evaluation options:

```
uv run evaluate.py --skip-judge          retrieval scores only (seconds)
uv run evaluate.py --k 2 --skip-judge    retrieve 2 chunks instead of 5
uv run evaluate.py --chunk-size 500      test smaller chunks (the default database is restored afterwards)
```

## Reading the scores

| Metric | Meaning | 🟢 Good | 🟡 OK |
|---|---|---|---|
| MRR | Is the first relevant chunk near the top? (1.0 = always first) | ≥ 0.90 | ≥ 0.75 |
| nDCG | Are all the relevant chunks ranked high? | ≥ 0.90 | ≥ 0.75 |
| Keyword coverage | Share of expected facts found in the retrieved chunks | ≥ 90% | ≥ 75% |
| Accuracy, Completeness, Relevance | Judge scores from 1 to 5 | ≥ 4.5 | ≥ 3.5 |

These thresholds are a rule of thumb for this project.

**About the judge:** it is the same small local model (llama3.2), so it scores more generously than a large model would. Treat its scores as a rough signal. The retrieval metrics are exact calculations.

## Settings (`config.py`)

| Setting | Default | Notes |
|---|---|---|
| `MODEL` | `llama3.2` | Any Ollama chat model you have pulled |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 1000 / 200 | Run `ingest.py` again after changing these |
| `TOP_K` | 5 | Chunks retrieved per question |
| `EMBEDDING_PROVIDER` | `huggingface` | Set to `ollama` if huggingface.co is blocked (run `ollama pull all-minilm` first, then run `ingest.py` again) |

## Use your own documents

1. Put your files into sub-folders of `knowledge_base/`. The folder name becomes the document type; files placed directly in `knowledge_base/` get the type `general`.
2. Run `uv run ingest.py`.
3. Update `evaluation/tests.jsonl` with questions, keywords and reference answers about your documents, and the example questions at the top of `app.py`.

| File type | Supported | Notes |
|---|---|---|
| `.md` Markdown | ✅ | Best results |
| `.txt` text | ✅ | UTF-8 or Windows encoding |
| `.pdf` PDF | ✅ | Read page by page, and the Sources line shows the page. **Scanned PDFs (images) have no text and are skipped.** Tables can come out a bit messy. |
| `.docx` Word | ✅ | Headings, lists and tables are kept. For old `.doc` files, open them in Word and save as `.docx`. |
| Other types (`.xlsx`, `.pptx`, images) | ❌ | Listed under **Skipped** in the ingest output |

Everything stays on your computer, but check your company's policy before using internal documents.

## Troubleshooting

| Problem | Fix |
|---|---|
| 🔴 *Can't reach Ollama* | Start the Ollama app (or run `ollama serve`) |
| *Ollama doesn't have the model* | `ollama pull llama3.2` |
| `ingest.py` is stuck at *Loading the embedding model* | huggingface.co may be blocked, so use `EMBEDDING_PROVIDER = "ollama"` (see Settings) |
| *The vector database is empty* | `uv run ingest.py` |
| The first answer is slow | Normal: llama3.2 is loading into memory (10 to 30 seconds) |
| `Failed to hardlink files` warning from uv | Harmless. To hide it, run `$env:UV_LINK_MODE="copy"` |
| Port 7860 is already in use | Another copy of the app is running. Close it with Ctrl + C. |
| A file is listed under **Skipped** | Check the reason: unsupported type, scanned PDF (no text) or a damaged file |
| Answers look wrong | `uv run rag.py "your question" --show-chunks` shows what was retrieved. The problem is usually retrieval, not the model. |
