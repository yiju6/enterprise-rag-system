from pathlib import Path

from app.ingestor import ingest, default_router, default_chunker
from app.chunker import DocumentChunker


def run_sanity_check(file_path: Path):
    print(f"\n=== Running sanity check for: {file_path.name} ===")

    # Parse → Chunk (reuse pipeline components for visibility into metrics)
    document = default_router.parse(file_path)
    chunks = default_chunker.chunk(document)

    # Compute metrics
    metrics = default_chunker.compute_metrics(chunks)

    print("Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    # Optional: run full ingestion (embeddings + ChromaDB)
    ingest(file_path)


if __name__ == "__main__":
    html_dir = Path("data/uploads/html")
    md_dir = Path("data/uploads/markdown")

    html_files = list(html_dir.glob("*"))
    md_files = list(md_dir.glob("*"))

    if html_files:
        run_sanity_check(html_files[0])
    else:
        print("No HTML files found.")

    if md_files:
        run_sanity_check(md_files[0])
    else:
        print("No Markdown files found.")