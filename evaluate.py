"""
evaluate.py: measure how good the assistant is.

Don't just demo a RAG system, score it:
  1. Retrieval quality: did we fetch the right chunks?  -> MRR, nDCG, keyword coverage
  2. Answer quality: is the answer right?              -> LLM-as-a-judge (1 to 5 scores)

Run it:
    uv run evaluate.py                    all tests, top 5 chunks, with the judge
    uv run evaluate.py --k 2              retrieve only 2 chunks (compare with --k 5)
    uv run evaluate.py --skip-judge       retrieval scores only (fast)
    uv run evaluate.py --chunk-size 500   re-ingest with smaller chunks, test, then restore
"""

if __name__ == "__main__":
    print("Starting the evaluation... (loading libraries)", flush=True)

import argparse
import json
import math
from datetime import datetime

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

import config
import ingest
import rag

SUMMARY_FILE = config.PROJECT_DIR / "eval_summary.csv"  # one line per run, for comparing settings


# Data models
# Pydantic models give the results a fixed structure, and the judge's
# JSON reply is checked against one (structured output).
class TestQuestion(BaseModel):
    question: str
    category: str
    keywords: list[str]
    reference_answer: str


class RetrievalEval(BaseModel):
    mrr: float
    ndcg: float
    keyword_coverage: float  # percent of the test's keywords found in the retrieved chunks


class AnswerEval(BaseModel):
    feedback: str = Field(description="One or two sentences explaining the scores")
    accuracy: float = Field(ge=1, le=5, description="Is the answer factually correct?")
    completeness: float = Field(ge=1, le=5, description="Does it cover every part of the question?")
    relevance: float = Field(ge=1, le=5, description="Does it answer directly, without extra noise?")


def load_tests(path=config.TESTS_FILE):
    with open(path, encoding="utf-8") as f:
        return [TestQuestion.model_validate_json(line) for line in f if line.strip()]


# 1. Retrieval metrics
# A chunk counts as relevant for a keyword if it contains that keyword.
def reciprocal_rank(keyword, chunks):
    """1 / position of the first chunk containing the keyword (0 if none do)."""
    for position, chunk in enumerate(chunks, start=1):
        if keyword.lower() in chunk.page_content.lower():
            return 1.0 / position
    return 0.0


def ndcg(keyword, chunks):
    """
    nDCG with yes/no relevance: relevant chunks near the top score more.
    DCG  = sum(relevance / log2(position + 1)) over the retrieved chunks (position starts at 1)
    nDCG = DCG divided by the best possible DCG for the same chunks.
    """
    relevance = [1 if keyword.lower() in c.page_content.lower() else 0 for c in chunks]
    dcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(relevance))
    ideal = sum(rel / math.log2(i + 2) for i, rel in enumerate(sorted(relevance, reverse=True)))
    return dcg / ideal if ideal > 0 else 0.0


def evaluate_retrieval(test, chunks):
    """MRR, nDCG and keyword coverage, averaged over the test's keywords."""
    rr = [reciprocal_rank(k, chunks) for k in test.keywords]
    found = sum(1 for score in rr if score > 0)
    return RetrievalEval(
        mrr=sum(rr) / len(rr),
        ndcg=sum(ndcg(k, chunks) for k in test.keywords) / len(test.keywords),
        keyword_coverage=100 * found / len(test.keywords),
    )


# 2. Answer quality: LLM-as-a-judge
JUDGE_SYSTEM_PROMPT = """You are a strict evaluator of answers from a knowledge assistant.
Compare the generated answer with the reference answer and score it from 1 (very poor) to 5 (ideal):
- accuracy: is it factually correct compared with the reference? If any fact is wrong, accuracy must be 1.
- completeness: does it cover every part of the question?
- relevance: does it answer the question directly, without unrelated information?
Only give 5 for a perfect answer.
Respond with JSON only, in this format:
{"feedback": "<one or two sentences>", "accuracy": <1-5>, "completeness": <1-5>, "relevance": <1-5>}"""


def judge_answer(test, generated_answer):
    """
    LLM-as-a-judge: a model grades another model's answer.
    Here the judge is the same local llama3.2, asked to reply in JSON that matches
    AnswerEval. If the JSON is broken we retry once, then report a judge error.
    """
    user_prompt = (
        f"Question:\n{test.question}\n\n"
        f"Reference answer:\n{test.reference_answer}\n\n"
        f"Generated answer:\n{generated_answer}"
    )
    last_error = None
    for _attempt in range(2):
        response = rag.client.chat.completions.create(
            model=config.MODEL,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "AnswerEval", "schema": AnswerEval.model_json_schema()},
            },
            temperature=0,
        )
        text = (response.choices[0].message.content or "").strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return AnswerEval.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as error:
            last_error = error
    raise ValueError(f"judge gave invalid JSON: {last_error}")


# Run all the tests
def run_evaluation(k=config.TOP_K, use_judge=True, progress=None):
    """
    Returns (results_table, averages). `progress(i, total, question)` is called
    before each test so the app can show a progress bar.
    """
    tests = load_tests()
    rows = []
    for i, test in enumerate(tests, start=1):
        if progress:
            progress(i, len(tests), test.question)

        row = {"#": i, "category": test.category, "question": test.question}
        answer, chunks = rag.answer_once(test.question, k=k)
        retrieval = evaluate_retrieval(test, chunks)
        row.update(
            mrr=round(retrieval.mrr, 3),
            ndcg=round(retrieval.ndcg, 3),
            keyword_coverage=round(retrieval.keyword_coverage, 1),
            answer=answer.strip(),
            sources=rag.sources_footer(chunks).replace(rag.SOURCES_MARKER, "").strip(),
        )

        if use_judge:
            try:
                verdict = judge_answer(test, answer)
                row.update(accuracy=verdict.accuracy, completeness=verdict.completeness,
                           relevance=verdict.relevance, feedback=verdict.feedback)
            except Exception as error:
                row.update(accuracy=None, completeness=None, relevance=None,
                           feedback=f"judge error: {error}")
        rows.append(row)

    table = pd.DataFrame(rows)
    averages = {
        "MRR": table["mrr"].mean(),
        "nDCG": table["ndcg"].mean(),
        "Keyword coverage (%)": table["keyword_coverage"].mean(),
    }
    if use_judge:
        for column in ("accuracy", "completeness", "relevance"):
            averages[column.capitalize() + " (1-5)"] = pd.to_numeric(table[column]).mean()
    return table, averages


def rating(metric, value):
    """Turn a number into a label, so results are easy to read."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "⚪ n/a"
    if "(1-5)" in metric:
        good, ok = 4.5, 3.5
    elif "(%)" in metric:
        good, ok = 90, 75
    else:
        good, ok = 0.9, 0.75
    return "🟢 Good" if value >= good else "🟡 OK" if value >= ok else "🔴 Low"


def save_results(table, averages, k, chunk_size, use_judge):
    table.to_csv(config.EVAL_RESULTS_FILE, index=False, encoding="utf-8-sig")  # opens cleanly in Excel
    summary = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "model": config.MODEL,
        "k": k,
        "chunk_size": chunk_size,
        "judge": "yes" if use_judge else "no",
        **{name: round(value, 3) for name, value in averages.items()},
    }
    new_row = pd.DataFrame([summary])
    if SUMMARY_FILE.exists():
        new_row = pd.concat([pd.read_csv(SUMMARY_FILE), new_row], ignore_index=True)
    new_row.to_csv(SUMMARY_FILE, index=False, encoding="utf-8-sig")


def print_report(table, averages, k, chunk_size):
    print()
    print("=" * 78)
    print(f" EVALUATION RESULTS   model={config.MODEL}   k={k}   chunk_size={chunk_size}")
    print("=" * 78)
    columns = ["#", "category", "mrr", "ndcg", "keyword_coverage"]
    columns += [c for c in ("accuracy", "completeness", "relevance") if c in table]
    print(table[columns].to_string(index=False))
    print("-" * 78)
    for name, value in averages.items():
        print(f" {name:<22} {value:6.3f}   {rating(name, value)}")
    print("-" * 78)
    if "feedback" in table:
        print(" Judge feedback:")
        for _, row in table.iterrows():
            print(f"  {row['#']:>2}. {row['feedback']}")
    print("=" * 78)
    print(f" Details saved to {config.EVAL_RESULTS_FILE.name}; run history in {SUMMARY_FILE.name}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate the Knowledge Assistant")
    parser.add_argument("--k", type=int, default=config.TOP_K, help="chunks to retrieve per question")
    parser.add_argument("--chunk-size", type=int, default=None, help="re-ingest with this chunk size first")
    parser.add_argument("--skip-judge", action="store_true", help="only score retrieval (much faster)")
    args = parser.parse_args()

    chunk_size = args.chunk_size or config.CHUNK_SIZE
    if args.chunk_size and args.chunk_size != config.CHUNK_SIZE:
        overlap = min(config.CHUNK_OVERLAP, args.chunk_size // 5)
        print(f"Re-ingesting with chunk_size={args.chunk_size}, overlap={overlap}...")
        print(f"  -> {ingest.ingest(args.chunk_size, overlap, verbose=False)['chunks']} chunks")

    def show_progress(i, total, question):
        print(f"[{i}/{total}] {question}", flush=True)

    try:
        table, averages = run_evaluation(args.k, not args.skip_judge, show_progress)
    except Exception as error:
        raise SystemExit(rag.friendly_error(error))
    finally:
        if args.chunk_size and args.chunk_size != config.CHUNK_SIZE:
            print(f"Restoring the default vector database (chunk_size={config.CHUNK_SIZE})...")
            ingest.ingest(verbose=False)

    save_results(table, averages, args.k, chunk_size, not args.skip_judge)
    print_report(table, averages, args.k, chunk_size)


if __name__ == "__main__":
    main()
