"""
rag.py: the "brain" of the assistant (Retrieval-Augmented Generation).

    question -> find the most similar chunks -> put them in the prompt -> LLM answers

The Gradio app (app.py) and the evaluation (evaluate.py) both use this file.

Test it from the terminal:
    uv run rag.py "What is the maximum photo upload size?"
    uv run rag.py "What is the maximum photo upload size?" --show-chunks   (also print the retrieved chunks)
    uv run rag.py                                          (ask several questions in a row)
"""

if __name__ == "__main__":
    print("Starting... (loading libraries)", flush=True)

import argparse
import sys

from openai import APIConnectionError, NotFoundError, OpenAI

import config
import vector_store

# Ollama speaks the OpenAI API, so the normal OpenAI client works;
# only base_url changes.
client = OpenAI(base_url=config.OLLAMA_BASE_URL, api_key=config.OLLAMA_API_KEY)

# The system prompt sets the rules. "Answer only from the context" and
# "say you don't know" stop the model from making things up.
SYSTEM_PROMPT = """You are a helpful knowledge assistant.
Answer only using the context below. If the answer is not in the context, say you don't know.
Keep answers short and clear.

Context:
{context}"""

SOURCES_MARKER = "\n\n📄 *Sources checked:*"

def get_store():
    # Opened fresh each time, so a re-ingest (e.g. by evaluate.py) is picked up straight away
    return vector_store.open_vector_store()


# Step 1: Retrieval
def retrieve(question, k=config.TOP_K):
    """
    Retrieval: the question is turned into a vector and Chroma returns the
    k chunks whose vectors are closest to it.
    """
    return get_store().similarity_search(question, k=k)


def text_of(content):
    """Get plain text from a chat message (Gradio can send text or a list of parts)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(text_of(part) for part in content)
    if isinstance(content, dict):
        return str(content.get("text", ""))
    return str(content or "")


def search_query(question, history):
    """
    Follow-up questions like "what about iOS?" don't mean much on their own.
    Adding the previous user question gives retrieval the missing topic.
    """
    previous = [text_of(m["content"]) for m in (history or []) if m.get("role") == "user"]
    return f"{previous[-1]}\n{question}" if previous else question


# Step 2: Build the prompt
def build_context(chunks):
    """Join the chunks into one block of text, each labelled with its file name."""
    return "\n\n".join(
        f"[Source: {vector_store.source_label(c.metadata)}]\n{c.page_content}" for c in chunks
    )


def build_messages(question, history, chunks):
    """
    The Chat Completions message list: one system message, then the
    conversation so far, then the new user question.
    The retrieved context goes into the system message.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(context=build_context(chunks))}]
    for m in history or []:
        if m.get("role") in ("user", "assistant"):
            content = text_of(m["content"]).split(SOURCES_MARKER)[0]  # drop our sources footer
            messages.append({"role": m["role"], "content": content})
    messages.append({"role": "user", "content": question})
    return messages


def sources_footer(chunks):
    """Unique file names in rank order; PDFs also list their pages, e.g. guide.pdf (p. 1, 3)."""
    pages = {}
    for c in chunks:
        found = pages.setdefault(c.metadata["source"], [])
        page = c.metadata.get("page")
        if page and page not in found:
            found.append(page)
    labels = [f"{name} (p. {', '.join(map(str, sorted(p)))})" if p else name for name, p in pages.items()]
    return f"{SOURCES_MARKER} " + ", ".join(labels)


def friendly_error(error):
    if isinstance(error, APIConnectionError):
        return (f"⚠️ Can't reach Ollama at {config.OLLAMA_BASE_URL}. "
                "Is the Ollama app running? (Start it, or run `ollama serve`.)")
    if isinstance(error, NotFoundError):
        return f"⚠️ Ollama doesn't have the model '{config.MODEL}'. Run: ollama pull {config.MODEL}"
    return f"⚠️ Something went wrong: {error}"


# Step 3: Ask the LLM
def answer(question, history=None):
    """
    Streaming answer, used by the Gradio app.
    Streaming shows the reply word by word as it arrives.
    Yields the full text so far each time (that's what Gradio expects).
    """
    chunks = retrieve(search_query(question, history))
    messages = build_messages(question, history, chunks)
    reply = ""
    try:
        stream = client.chat.completions.create(
            model=config.MODEL, messages=messages, stream=True, temperature=0.2
        )
        for part in stream:
            if part.choices and part.choices[0].delta.content:
                reply += part.choices[0].delta.content
                yield reply
    except Exception as error:  # show a clear message instead of crashing the app
        yield reply + friendly_error(error)
        return
    yield reply + sources_footer(chunks)


def answer_once(question, history=None, k=config.TOP_K):
    """
    Non-streaming answer, used by the evaluation.
    Returns (answer_text, retrieved_chunks).
    """
    chunks = retrieve(search_query(question, history), k=k)
    messages = build_messages(question, history, chunks)
    response = client.chat.completions.create(model=config.MODEL, messages=messages, temperature=0.2)
    return response.choices[0].message.content, chunks


# Terminal test mode
def print_chunks(chunks):
    print("\n--- Retrieved chunks (best match first) ---")
    for rank, c in enumerate(chunks, start=1):
        preview = c.page_content[:120].replace("\n", " ")
        print(f" {rank}. [{c.metadata['doc_type']}/{vector_store.source_label(c.metadata)}] {preview}...")
    print("-------------------------------------------\n")


def ask_in_terminal(question, history, show_chunks):
    if show_chunks:
        print_chunks(retrieve(search_query(question, history)))
    print("🤖 ", end="", flush=True)
    printed = ""
    for text in answer(question, history):
        text = text.replace("*Sources checked:*", "Sources checked:")  # no markdown in the terminal
        print(text[len(printed):], end="", flush=True)
        printed = text
    print("\n")
    history += [{"role": "user", "content": question}, {"role": "assistant", "content": printed}]


def main():
    parser = argparse.ArgumentParser(description="Ask the Knowledge Assistant from the terminal")
    parser.add_argument("question", nargs="?", help="your question (leave empty for chat mode)")
    parser.add_argument("--show-chunks", action="store_true", help="print the retrieved chunks")
    args = parser.parse_args()

    if get_store()._collection.count() == 0:
        sys.exit("The vector database is empty. Run `uv run ingest.py` first.")

    history = []
    if args.question:
        ask_in_terminal(args.question, history, args.show_chunks)
        return

    print(f"Knowledge Assistant (model: {config.MODEL}). Press Enter on an empty line to quit.\n")
    while True:
        question = input("🧑 You: ").strip()
        if not question:
            break
        ask_in_terminal(question, history, args.show_chunks)


if __name__ == "__main__":
    main()
