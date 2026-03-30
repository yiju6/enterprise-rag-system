from __future__ import annotations

import json
from pathlib import Path
from app.models import Document
from app.ingestor import ingest, default_router, default_chunker


PROJECT_ROOT = Path(__file__).resolve().parents[1]

HTML_DIR = PROJECT_ROOT / "data" / "uploads" / "html"
MARKDOWN_DIR = PROJECT_ROOT / "data" / "uploads" / "markdown"
PDF_DIR = PROJECT_ROOT / "data" / "uploads" / "pdf"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "ingestion_sanity_check" / "results.json"


def run_sanity_check(file_path: Path) -> dict:
    document = default_router.parse(file_path)
    chunks = default_chunker.chunk(document)
    metrics = default_chunker.compute_metrics(chunks)

    result = {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "doc_type": document.doc_type,
        "source_file": document.source_file,
        "document_metadata": document.metadata,
        "metrics": metrics,
    }

    print(f"\n=== Running sanity check for: {file_path.name} ===")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    return result


def find_common_basenames(html_dir: Path, markdown_dir: Path, pdf_dir: Path) -> set[str]:
    html_names = {f.stem for f in html_dir.glob("*.html")} | {f.stem for f in html_dir.glob("*.htm")}
    markdown_names = {f.stem for f in markdown_dir.glob("*.md")} | {f.stem for f in markdown_dir.glob("*.markdown")}
    pdf_names = {f.stem for f in pdf_dir.glob("*.pdf")}

    return html_names & markdown_names & pdf_names


def build_file_map(base_name: str) -> dict[str, Path]:
    html_path = HTML_DIR / f"{base_name}.html"
    if not html_path.exists():
        html_path = HTML_DIR / f"{base_name}.htm"

    markdown_path = MARKDOWN_DIR / f"{base_name}.md"
    if not markdown_path.exists():
        markdown_path = MARKDOWN_DIR / f"{base_name}.markdown"

    pdf_path = PDF_DIR / f"{base_name}.pdf"

    return {
        "html": html_path,
        "markdown": markdown_path,
        "pdf": pdf_path,
    }


def main() -> None:
    common_names = find_common_basenames(HTML_DIR, MARKDOWN_DIR, PDF_DIR)
    
    if not common_names:
        raise FileNotFoundError(...)

    all_results = {"results": []}

    for base_name in sorted(common_names):
        files = build_file_map(base_name)
        print(f"\nFound common document set: {base_name}")

        for doc_type, file_path in files.items():
            if not file_path.exists():
                raise FileNotFoundError(f"Missing {doc_type} file: {file_path}")
            result = run_sanity_check(file_path)
            all_results["results"].append(result)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved metrics to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()