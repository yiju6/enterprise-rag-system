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

    NON_TICKER_TOKENS: ClassVar[set[str]] = {
        "SEC",
        "10Q",
        "10K",
        "FY",
        "ANNUAL",
        "QUARTERLY",
    }

    def __init__(self) -> None:
        self.converter = DocumentConverter()

    def _parse_filename(self, file_path: Path) -> tuple[str, str]:
        """
        Parse company ticker and quarter from filename.

        Examples:
        - AAPL_2024_Q1.pdf
        - AAPL-Q1-2024.pdf
        - 2022 Q3 AAPL.pdf
        - AAPL_SEC_2024_Q1.pdf

        Returns:
            (company, quarter), e.g. ("AAPL", "Q1 2024")
        """
        stem = file_path.stem.strip()
        if not stem:
            raise InvalidPDFFileNameError(f"Empty filename: {file_path.name}")

        normalized = re.sub(r"[-\s]+", "_", stem)
        normalized = re.sub(r"_+", "_", normalized).strip("_")

        quarter_match = re.search(r"(20\d{2})_(Q[1-4])", normalized, re.IGNORECASE)
        if quarter_match:
            year = quarter_match.group(1)
            q = quarter_match.group(2).upper()
            quarter = f"{q} {year}"
        else:
            quarter_match = re.search(r"(Q[1-4])_(20\d{2})", normalized, re.IGNORECASE)
            if quarter_match:
                q = quarter_match.group(1).upper()
                year = quarter_match.group(2)
                quarter = f"{q} {year}"
            else:
                raise InvalidPDFFileNameError(
                    f"Could not parse quarter from filename: {file_path.name}"
                )

        tokens = [t for t in normalized.split("_") if t]
        for token in tokens:
            upper_token = token.upper()

            if upper_token in self.NON_TICKER_TOKENS:
                continue
            if re.fullmatch(r"Q[1-4]", upper_token):
                continue
            if re.fullmatch(r"20\d{2}", upper_token):
                continue
            if re.fullmatch(r"[A-Z]{1,10}", upper_token):
                return upper_token, quarter

        raise InvalidPDFFileNameError(
            f"Could not parse company ticker from filename: {file_path.name}"
        )

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