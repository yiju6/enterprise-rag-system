from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from docling.document_converter import DocumentConverter
from docling_core.types.doc import TableItem
from .base_parser import BaseParser
from .exceptions import InvalidPDFFileNameError
from .models import Block, Document


class PDFParser(BaseParser):
    supported_extensions: ClassVar[list[str]] = [".pdf"]
    magic_bytes: ClassVar[bytes | None] = b"%PDF"

    def __init__(self) -> None:
        self.converter = DocumentConverter()

    def _extract_page_number(self, item) -> int | None:
        prov = getattr(item, "prov", None)
        if not prov:
            return None

        if isinstance(prov, list) and prov:
            return getattr(prov[0], "page_no", None)

        return getattr(prov, "page_no", None)

    def _extract_text(self, item) -> str | None:
        for attr in ("text", "orig", "raw_text", "content"):
            value = getattr(item, attr, None)
            if value:
                text = str(value).strip()
                if text:
                    return text
        return None

    def _extract_table_content(self, item, doc) -> str | None:
        """
        Export table as markdown for readable structured content.
        """
        if isinstance(item, TableItem):
            try:
                markdown = item.export_to_markdown(doc=doc)
                if markdown and markdown.strip():
                    return markdown.strip()
            except Exception:
                pass

            try:
                df = item.export_to_dataframe(doc=doc)
                if df is not None and not df.empty:
                    return df.to_markdown(index=False)
            except Exception:
                pass

        return None

    def _clean_metadata(self, metadata: dict) -> dict:
        return {k: v for k, v in metadata.items() if v is not None}

    def parse(self, file_path: Path) -> Document:
        company, quarter = self._parse_filename(file_path)

        result = self.converter.convert(str(file_path))
        doc = result.document

        blocks: list[Block] = []
        current_section: str | None = None

        for item, _level in doc.iterate_items():
            label = getattr(item, "label", None)
            item_type = getattr(label, "value", str(label)).lower() if label else "unknown"

            if item_type == "section_header":
                heading_text = self._extract_text(item)
                if heading_text:
                    current_section = heading_text
                continue

            if item_type == "picture":
                continue

            page_number = self._extract_page_number(item)

            if isinstance(item, TableItem) or item_type == "table":
                table_content = self._extract_table_content(item, doc)
                if not table_content:
                    continue

                blocks.append(
                    Block(
                        content=table_content,
                        content_type="table",
                        metadata=self._clean_metadata(
                            {
                                "section": current_section,
                                "page_number": page_number,
                            }
                        ),
                    )
                )
                continue

            text = self._extract_text(item)
            if not text:
                continue

            blocks.append(
                Block(
                    content=text,
                    content_type="text",
                    metadata=self._clean_metadata(
                        {
                            "section": current_section,
                            "page_number": page_number,
                            "docling_label": item_type,
                        }
                    ),
                )
            )

        return Document(
            source_file=file_path.name,
            doc_type="pdf",
            blocks=blocks,
            metadata=self._clean_metadata(
                {
                    "company": company,
                    "quarter": quarter,
                }
            ),
        )