from pathlib import Path
from typing import Sequence

from .base_parser import BaseParser
from ..exceptions import UnsupportedFileTypeError
from ..models import Document


class ParserRouter:
    """Routes a file to the appropriate parser."""

    def __init__(self, parsers: Sequence[BaseParser]):
        self.parsers = parsers

    def parse(self, file_path: Path) -> Document:
        """
        Find a parser that can handle the file and run parse().
        """
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser.parse(file_path)

        raise UnsupportedFileTypeError(f"No parser found for file: {file_path}")