"""
ingest.py: turn our documents into a searchable vector database.

    documents  ->  chunks  ->  vectors (embeddings)  ->  Chroma (vector_db/)

Supported files in knowledge_base/: .md, .txt, .pdf (text PDFs, not scans) and .docx (Word).

Run it:
    uv run ingest.py
    uv run ingest.py --chunk-size 500 --chunk-overlap 100   (try other settings)
"""

if __name__ == "__main__":
    print("Starting ingest... (the first run can take a few minutes to load the libraries)", flush=True)

import argparse
from collections import Counter
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config
import vector_store


# Loading files
# One small reader per file type. Each returns a list of (text, page_number)
# pairs; page_number is None for files that have no pages.
def read_markdown(file):
    return [(file.read_text(encoding="utf-8"), None)]  # utf-8 matters on Windows


def read_text(file):
    """Plain .txt files: try UTF-8 first, then the usual Windows encoding."""
    try:
        return [(file.read_text(encoding="utf-8"), None)]
    except UnicodeDecodeError:
        return [(file.read_text(encoding="cp1252"), None)]


def read_pdf(file):
    """PDF files: one piece of text per page, so answers can say which page they came from."""
    from pypdf import PdfReader

    reader = PdfReader(file)
    return [(page.extract_text() or "", number) for number, page in enumerate(reader.pages, start=1)]


def read_word(file):
    """
    Word (.docx) files: headings become markdown headings (#, ##), and tables
    become "cell | cell" lines, so the text keeps its structure.
    """
    import docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    document = docx.Document(file)
    lines = []
    for block in document.element.body.iterchildren():
        tag = block.tag.rsplit("}", 1)[-1]
        if tag == "p":
            paragraph = Paragraph(block, document)
            text = paragraph.text.strip()
            if not text:
                continue
            style = paragraph.style.name if paragraph.style is not None else ""
            if style.startswith("Heading") and style[-1:].isdigit():
                text = "#" * int(style[-1]) + " " + text
            elif "List" in style:
                text = "- " + text
            lines.append(text)
        elif tag == "tbl":
            for row in Table(block, document).rows:
                lines.append(" | ".join(cell.text.strip() for cell in row.cells))
    return [("\n\n".join(lines), None)]


READERS = {
    ".md": read_markdown,
    ".txt": read_text,
    ".pdf": read_pdf,
    ".docx": read_word,
}


def load_documents(folder: Path = config.KNOWLEDGE_BASE_DIR, report=None) -> list[Document]:
    """
    Read every supported file (.md, .txt, .pdf, .docx) in the knowledge base
    and wrap it in LangChain Documents.

    Each document carries metadata. The sub-folder name becomes "doc_type"
    (processes, team, ...), which is used later to colour the vector map.
    PDFs also get a "page" number, which is shown in the Sources line.

    LangChain's DirectoryLoader could do this too, but it lives in the
    langchain-community package, which is being retired, so the files are
    read here directly. The result is the same kind of list of Documents.

    `report` (optional dict) is filled with what was loaded and what was skipped.
    """
    report = report if report is not None else {}
    report.update(files=Counter(), skipped=[])
    documents = []

    for file in sorted(p for p in folder.rglob("*") if p.is_file()):
        if file.name.startswith(("~$", ".")):  # Word lock files, hidden files
            continue
        reader = READERS.get(file.suffix.lower())
        if reader is None:
            report["skipped"].append(f"{file.name} (file type not supported)")
            continue

        try:
            pieces = reader(file)
        except Exception as error:
            report["skipped"].append(f"{file.name} (could not be read: {error})")
            continue

        pieces = [(text, page) for text, page in pieces if text.strip()]
        if not pieces:
            hint = ", probably a scanned PDF" if file.suffix.lower() == ".pdf" else ""
            report["skipped"].append(f"{file.name} (no text found{hint})")
            continue

        sub_folders = file.parent.relative_to(folder).parts
        for text, page in pieces:
            metadata = {
                "source": file.name,                                    # e.g. release-checklist.md
                "doc_type": sub_folders[0] if sub_folders else "general",  # e.g. processes
                "file_type": file.suffix.lower().lstrip("."),          # md, pdf, docx, txt
            }
            if page is not None:
                metadata["page"] = page                                 # PDFs only
            documents.append(Document(page_content=text, metadata=metadata))
        report["files"][file.suffix.lower()] += 1

    return documents


def split_into_chunks(documents, chunk_size, chunk_overlap):
    """
    Chunking: long documents are cut into smaller pieces so only the relevant
    pieces are sent to the LLM. The overlap repeats a little text between
    neighbouring chunks so an idea isn't cut in half.
    RecursiveCharacterTextSplitter tries to cut at paragraphs first, then
    lines, then sentences, so chunks stay readable.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(documents)


def store_chunks(chunks):
    """
    Embed every chunk and save the vectors in Chroma.
    We delete the old collection first, so running this script again is safe.
    """
    old_store = vector_store.open_vector_store()
    old_store.delete_collection()

    store = vector_store.open_vector_store()  # a fresh, empty collection
    store.add_documents(chunks)
    return store


def ingest(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP, verbose=True) -> dict:
    """Run the whole pipeline and return a small summary (evaluate.py uses this too)."""
    report = {}
    documents = load_documents(report=report)
    if not documents:
        raise SystemExit(f"No readable files found in {config.KNOWLEDGE_BASE_DIR}")
    chunks = split_into_chunks(documents, chunk_size, chunk_overlap)
    store = store_chunks(chunks)

    # Read one vector back to show how many numbers each chunk became
    collection = store._collection
    sample = collection.get(limit=1, include=["embeddings"])["embeddings"][0]

    summary = {
        "files": sum(report["files"].values()),
        "files_by_type": report["files"],
        "skipped": report["skipped"],
        "documents": len(documents),
        "chunks": collection.count(),
        "dimensions": len(sample),
        "chunks_per_type": Counter(c.metadata["doc_type"] for c in chunks),
    }

    if verbose:
        print_summary(documents, chunks, summary, chunk_size, chunk_overlap)
    return summary


def print_summary(documents, chunks, summary, chunk_size, chunk_overlap):
    doc_types = sorted({d.metadata["doc_type"] for d in documents})
    by_type = ", ".join(f"{n} {ext}" for ext, n in sorted(summary["files_by_type"].items()))
    print()
    print("=" * 60)
    print(" INGEST COMPLETE")
    print("=" * 60)
    print(f" Files loaded     : {summary['files']}  ({by_type})")
    print(f" Folders          : {', '.join(doc_types)}")
    print(f" Chunks created   : {summary['chunks']}  (chunk_size={chunk_size}, overlap={chunk_overlap})")
    print(f" Vector dimensions: {summary['dimensions']}")
    print(f" Saved to         : {config.VECTOR_DB_DIR}")
    print("-" * 60)
    print(" Chunks per folder:")
    for doc_type, count in sorted(summary["chunks_per_type"].items()):
        print(f"   {doc_type:<14} {'#' * count} {count}")
    if summary["skipped"]:
        print("-" * 60)
        print(" Skipped:")
        for item in summary["skipped"]:
            print(f"   ! {item}")
    print("-" * 60)
    example = chunks[0]
    preview = example.page_content[:150].replace("\n", " ")
    print(f" Example chunk from {example.metadata['source']}:")
    print(f"   \"{preview}...\"")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Build the vector database from knowledge_base/")
    parser.add_argument("--chunk-size", type=int, default=config.CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=config.CHUNK_OVERLAP)
    args = parser.parse_args()

    print(f"Loading the embedding model via {config.EMBEDDING_PROVIDER} "
          "(the first run downloads it, please wait)...", flush=True)
    ingest(args.chunk_size, args.chunk_overlap)


if __name__ == "__main__":
    main()
