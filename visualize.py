"""
visualize.py: draw a map of the vector database.

Each chunk is a vector of 384 numbers. People can't picture 384 dimensions,
so we squash them down to 2 (or 3) with t-SNE and draw one dot per chunk.
Chunks with similar meaning land close together.

Run it (after ingest.py):
    uv run visualize.py          2D map
    uv run visualize.py --3d     3D map you can rotate
"""

if __name__ == "__main__":
    print("Starting visualize... (loading libraries)", flush=True)

import argparse
import textwrap
import webbrowser

import numpy as np
import plotly.graph_objects as go
from sklearn.manifold import TSNE

import config
import vector_store

# Colours and shapes for the folders (doc_type), given out in alphabetical order.
# The colour set was checked for colour-blind safety; every folder also gets
# its own marker shape and a text label, so colour is never the only clue.
STYLES = [
    {"color": "#2a78d6", "symbol": "circle"},
    {"color": "#eda100", "symbol": "square"},
    {"color": "#1baf7a", "symbol": "diamond"},
    {"color": "#4a3aa7", "symbol": "triangle-up"},
    {"color": "#e87ba4", "symbol": "cross"},
]
# Folders beyond the fifth are grey and told apart by shape and label
FALLBACK_STYLES = [
    {"color": "#52514e", "symbol": symbol}
    for symbol in ("circle-open", "square-open", "diamond-open", "x")
]
# 3D maps support fewer marker shapes, so swap the ones they don't have
SYMBOL_3D = {"triangle-up": "circle-open", "cross": "diamond-open"}

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e6e5e1"


def load_vectors():
    """Read every chunk, its vector and its metadata back out of Chroma."""
    store = vector_store.open_vector_store()
    data = store._collection.get(include=["embeddings", "documents", "metadatas"])
    vectors = np.array(data["embeddings"])
    if len(vectors) == 0:
        raise SystemExit("The vector database is empty. Run `uv run ingest.py` first.")
    return vectors, data["documents"], data["metadatas"]


def reduce_dimensions(vectors, n_components):
    """
    t-SNE squashes high-dimensional vectors (384 numbers) into 2 or 3 numbers
    while keeping similar vectors close together.
    Perplexity roughly means "how many neighbours each dot looks at"; it must be
    smaller than the number of chunks, so we scale it to our small dataset.
    """
    perplexity = min(30, max(2, (len(vectors) - 1) // 3))
    tsne = TSNE(n_components=n_components, perplexity=perplexity, random_state=42, init="pca")
    return tsne.fit_transform(vectors)


def hover_text(document, metadata):
    preview = textwrap.shorten(document.replace("\n", " "), width=100, placeholder="...")
    preview = "<br>".join(textwrap.wrap(preview, width=50))
    return (
        f"<b>{metadata['doc_type']}</b> · {vector_store.source_label(metadata)}"
        f"<br><span style='color:{TEXT_SECONDARY}'>{preview}</span>"
    )


def build_figure(points, documents, metadatas, three_d):
    doc_types = sorted({m["doc_type"] for m in metadatas})
    fig = go.Figure()

    for number, doc_type in enumerate(doc_types):
        idx = [i for i, m in enumerate(metadatas) if m["doc_type"] == doc_type]
        if number < len(STYLES):
            style = STYLES[number]
        else:
            style = FALLBACK_STYLES[(number - len(STYLES)) % len(FALLBACK_STYLES)]
        texts = [hover_text(documents[i], metadatas[i]) for i in idx]
        marker = dict(
            color=style["color"],
            symbol=SYMBOL_3D.get(style["symbol"], style["symbol"]) if three_d else style["symbol"],
            size=12 if not three_d else 6,
            line=dict(color=SURFACE, width=2),  # thin ring so overlapping dots stay distinct
        )
        name = f"{doc_type} ({len(idx)})"

        if three_d:
            fig.add_trace(go.Scatter3d(
                x=points[idx, 0], y=points[idx, 1], z=points[idx, 2],
                mode="markers", name=name, marker=marker,
                hovertext=texts, hoverinfo="text",
            ))
        else:
            fig.add_trace(go.Scatter(
                x=points[idx, 0], y=points[idx, 1],
                mode="markers", name=name, marker=marker,
                hovertext=texts, hoverinfo="text",
            ))
            # Direct label on the most central dot of each group (colour is never the only clue)
            group = points[idx, :2]
            centre = group[np.argmin(((group - group.mean(axis=0)) ** 2).sum(axis=1))]
            fig.add_annotation(
                x=float(centre[0]), y=float(centre[1]),
                text=f"<b>{doc_type}</b>", showarrow=False, yshift=22,
                font=dict(size=13, color=TEXT_PRIMARY),
                bgcolor="rgba(252,252,251,0.85)", borderpad=3,
            )

    total = len(documents)
    dims = "3" if three_d else "2"
    fig.update_layout(
        title=dict(
            text=(
                f"Knowledge base vector map: {total} chunks, 384 → {dims} dimensions (t-SNE)"
                f"<br><sup style='color:{TEXT_SECONDARY}'>Each dot is one chunk. "
                "Dots close together have similar meaning. Hover a dot to read it. "
                "The axes have no units.</sup>"
            ),
            font=dict(size=18, color=TEXT_PRIMARY),
            x=0.02,
        ),
        font=dict(family="Segoe UI, Inter, Arial, sans-serif", color=TEXT_PRIMARY),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        legend=dict(title=dict(text="Folder (doc_type)"), bgcolor=SURFACE,
                    font=dict(color=TEXT_SECONDARY)),
        hoverlabel=dict(bgcolor="white", bordercolor=GRID, font=dict(color=TEXT_PRIMARY)),
        margin=dict(l=40, r=40, t=90, b=40),
        width=1000, height=700,
    )
    axis = dict(showticklabels=False, title="", zeroline=False, gridcolor=GRID, showline=False)
    if three_d:
        axis_3d = dict(axis, backgroundcolor=SURFACE, showbackground=True)
        fig.update_scenes(xaxis=axis_3d, yaxis=axis_3d, zaxis=axis_3d, bgcolor=SURFACE)
    else:
        fig.update_xaxes(**axis)
        fig.update_yaxes(**axis)
    return fig


def main():
    parser = argparse.ArgumentParser(description="Draw a t-SNE map of the vector database")
    parser.add_argument("--3d", dest="three_d", action="store_true", help="draw a 3D map")
    parser.add_argument("--no-open", action="store_true", help="don't open the browser")
    args = parser.parse_args()

    vectors, documents, metadatas = load_vectors()
    print(f"Loaded {len(vectors)} vectors with {vectors.shape[1]} dimensions each.")

    points = reduce_dimensions(vectors, 3 if args.three_d else 2)
    fig = build_figure(points, documents, metadatas, args.three_d)

    # include_plotlyjs=True puts everything in one file, so it works offline
    fig.write_html(config.VECTOR_MAP_FILE, include_plotlyjs=True)
    print(f"Vector map saved to: {config.VECTOR_MAP_FILE}")

    if not args.no_open:
        webbrowser.open(config.VECTOR_MAP_FILE.as_uri())
        print("Opening it in your browser...")


if __name__ == "__main__":
    main()
