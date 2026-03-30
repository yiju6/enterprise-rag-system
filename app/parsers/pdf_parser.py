from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from .docling_base_parser import DoclingBaseParser
from ..models import Document


class PDFParser(DoclingBaseParser):
    supported_extensions: ClassVar[list[str]] = [".pdf"]
    magic_bytes: ClassVar[bytes | None] = b"%PDF"
    doc_type: ClassVar[str] = "pdf"

    def parse(self, file_path: Path) -> Document:
        company, quarter = self._parse_filename(file_path)
        return self._parse_docling_doc(
            file_path=file_path,
            doc_type=self.doc_type,
            company=company,
            quarter=quarter,
        )