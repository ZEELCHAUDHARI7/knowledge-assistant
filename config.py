"""
config.py: every setting for the Knowledge Assistant, in one place.

Change a value here and every script (ingest, app, evaluation) picks it up.
"""

import os
from pathlib import Path

# Folders and files
PROJECT_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = PROJECT_DIR / "knowledge_base"   # our source documents
VECTOR_DB_DIR = PROJECT_DIR / "vector_db"             # Chroma saves its data here
VECTOR_MAP_FILE = PROJECT_DIR / "vector_map.html"     # output of visualize.py
EVAL_DIR = PROJECT_DIR / "evaluation"
TESTS_FILE = EVAL_DIR / "tests.jsonl"                 # evaluation questions
EVAL_RESULTS_FILE = PROJECT_DIR / "eval_results.csv"  # output of evaluate.py

# The LLM
# An open-source model runs locally in Ollama. Ollama speaks the OpenAI API,
# so the normal OpenAI Python client works; only base_url and api_key change.
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_API_KEY = "ollama"  # Ollama ignores the key, but the client needs a value
MODEL = os.getenv("MODEL", "llama3.2")

# Embeddings
# A free HuggingFace embedding model that runs on the laptop.
# It turns each chunk into a list of 384 numbers (a vector).
#
# EMBEDDING_PROVIDER picks where the model is downloaded from:
#   "huggingface": the default (downloads from huggingface.co)
#   "ollama":      the SAME all-MiniLM model, served by Ollama.
#                   Use this if huggingface.co is blocked on your network:
#                   1) run:  ollama pull all-minilm
#                   2) set EMBEDDING_PROVIDER = "ollama"
#                   3) run:  uv run ingest.py   (always re-ingest after switching)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "huggingface")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # used by "huggingface"
OLLAMA_EMBEDDING_MODEL = "all-minilm"                        # used by "ollama"
COLLECTION_NAME = "documents"

# Chunking and retrieval
# Documents are split into overlapping chunks, and the top k most similar
# chunks are fetched for each question.
CHUNK_SIZE = 1000     # characters per chunk
CHUNK_OVERLAP = 200   # characters shared between neighbouring chunks
TOP_K = 5             # how many chunks to retrieve for each question
