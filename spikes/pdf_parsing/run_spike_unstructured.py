from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Table
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(BASE_DIR, "..", "..", "data", "uploads", "2022 Q3 AAPL.pdf")

elements = partition_pdf(filename=pdf_path, strategy="fast", page_numbers= [6, 9, 17])

output_path = os.path.join(BASE_DIR, "output", "results_unstructured.json")

output = {"6":{"Tables": [], "NarrativeText": [], "Title": []}, "9": {"Tables": [], "NarrativeText": [], "Title": []}, "17": {"Tables": [], "NarrativeText": [], "Title": []}}

for el in elements:
    page_num = el.metadata.page_number
    page_key = str(page_num)
    print(f"page_num={page_num}, page_key={page_key}, type={type(el).__name__}")
    if page_key not in output:
        continue  # Skip elements from pages not in the output dict
    if isinstance(el, Table):
        output[page_key]["Tables"].append({
            "type": type(el).__name__,
            "text": el.text,
            "text_as_html": el.metadata.text_as_html,
            "page_number": el.metadata.page_number
            })
    elif type(el).__name__ == "NarrativeText":
        output[page_key]["NarrativeText"].append({
            "type": type(el).__name__,
            "text": el.text,
            "page_number": el.metadata.page_number
        })
    else:
        output[page_key]["Title"].append({
            "type": type(el).__name__,
            "text": el.text,
            "text_as_html": el.metadata.text_as_html,
            "page_number": el.metadata.page_number
        })

if __name__ == "__main__":
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
