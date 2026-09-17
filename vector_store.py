"""
vector_store.py: everything about the vector database, in one place.

ingest.py, visualize.py and rag.py all use these two helpers, so they
always use the same embedding model and the same Chroma collection.
"""

import os

# Keep the console output clean for beginners:
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")               # Chroma usage stats off
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")        # harmless Windows warning
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from openai import OpenAI

import config

_embeddings = None  # created once, then reused (loading the model takes a few seconds)


class OllamaEmbeddings(Embeddings):
    """
    The same all-MiniLM embedding model, served by Ollama instead of HuggingFace.
    Ollama speaks the OpenAI API, so the normal OpenAI client can ask it
    for embeddings too.
    """

    def __init__(self):
        self.client = OpenAI(base_url=config.OLLAMA_BASE_URL, api_key=config.OLLAMA_API_KEY)

    def embed_documents(self, texts):
        response = self.client.embeddings.create(model=config.OLLAMA_EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]

    def embed_query(self, text):  # required by LangChain; Chroma uses it to embed questions
        return self.embed_documents([text])[0]


def get_embeddings():
    """
    An embedding model turns text into a vector (a list of numbers).
    Texts with similar meaning get vectors that are close together.
    We use the free all-MiniLM-L6-v2 model, which runs on the laptop and
    returns 384 numbers per text.
    The first run downloads the model (about 90 MB); later runs use the cached copy.
    """
    global _embeddings
    if _embeddings is None:
        if config.EMBEDDING_PROVIDER == "ollama":
            _embeddings = OllamaEmbeddings()
        else:
            # Imported here because it loads PyTorch, which is slow to start
            from langchain_huggingface import HuggingFaceEmbeddings

            _embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
    return _embeddings


def open_vector_store():
    """
    Chroma is the vector database. It stores every chunk with its vector and
    metadata, and can find the chunks closest to a question.
    """
    return Chroma(
        collection_name=config.COLLECTION_NAME,
        persist_directory=str(config.VECTOR_DB_DIR),
        embedding_function=get_embeddings(),
    )


def source_label(metadata):
    """'release-checklist.md', or 'notifications-module.pdf (p. 2)' for PDFs."""
    page = metadata.get("page")
    return f"{metadata['source']} (p. {page})" if page else metadata["source"]
