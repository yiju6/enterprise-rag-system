from __future__ import annotations
import json
from pathlib import Path
from docling.document_converter import DocumentConverter
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = Path(BASE_DIR) / ".." / ".." / "data" / "uploads" / "2022 Q3 AAPL.pdf"
OUTPUT_PATH = Path(BASE_DIR) / "output" / "results_docling.json"

TARGET_PAGES = [6, 9, 17]

def bbox_to_list(bbox):
    if bbox is None:
        return None

    for attrs in (("l", "t", "r", "b"), ("x0", "y0", "x1", "y1")):
        if all(hasattr(bbox, a) for a in attrs):
            return [float(getattr(bbox, a)) for a in attrs]

    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        return [float(x) for x in bbox]

    return None


def extract_content(item):
    if hasattr(item, "text") and item.text:
        return item.text

    for attr in ("orig", "raw_text", "content"):
        if hasattr(item, attr):
            value = getattr(item, attr)
            if value:
                return str(value)

    return None


def extract_bbox(item):
    prov = getattr(item, "prov", None)
    if not prov:
        return None

    if isinstance(prov, list) and prov:
        first = prov[0]
        return bbox_to_list(getattr(first, "bbox", None))

    return bbox_to_list(getattr(prov, "bbox", None))


def serialize_table_item(item, doc):
    """
    Export structured table content from a Docling TableItem.

    Prefer:
    - markdown for human inspection
    - dataframe -> records for structured review
    """
    table_markdown = None
    table_data = None

    try:
        table_markdown = item.export_to_markdown(doc=doc)
    except Exception:
        table_markdown = None

    try:
        df = item.export_to_dataframe(doc=doc)
        table_data = df.to_dict(orient="records")
    except Exception:
        table_data = None

    return {
        "table_markdown": table_markdown,
        "table_data": table_data,
    }


def main():
    converter = DocumentConverter()
    results = {
        "source_file": str(PDF_PATH),
        "parser": "docling",
        "pages": {},
    }

    for page_num in TARGET_PAGES:
        conv_result = converter.convert(PDF_PATH, page_range=(page_num, page_num))
        doc = conv_result.document

        page_items = []
        for item, _level in doc.iterate_items():
            label = getattr(item, "label", None)
            item_type = getattr(label, "value", str(label)).lower() if label else "unknown"

            record = {
                "type": item_type,
                "content": extract_content(item),
                "bbox": extract_bbox(item),
            }

            if item_type == "table":
                record.update(serialize_table_item(item, doc))
            else:
                record["table_markdown"] = None
                record["table_data"] = None

            page_items.append(record)

        results["pages"][str(page_num)] = page_items

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved results to {str(OUTPUT_PATH)}")


if __name__ == "__main__":
    main()