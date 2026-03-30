from pathlib import Path
from docling.document_converter import DocumentConverter


def batch_convert(input_dir: Path, output_dir: Path):
    converter = DocumentConverter()

    for file_path in input_dir.glob("*"):
        if file_path.suffix.lower() not in {".pdf", ".html", ".htm"}:
            continue

        output_path = output_dir / (file_path.stem + ".md")

        try:
            result = converter.convert(str(file_path))
            markdown = result.document.export_to_markdown()

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")

            print(f"✓ {file_path.name}")
        except Exception as e:
            print(f"✗ {file_path.name}: {e}")


if __name__ == "__main__":
    batch_convert(
        Path("data/raw"),
        Path("data/markdown"),
    )