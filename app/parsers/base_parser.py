from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from ..models import Document
import re
from ..exceptions import InvalidFileNameError

import inspect



class BaseParser(ABC):
    """Base interface for all parsers."""

    supported_extensions: ClassVar[list[str] | None] = None
    magic_bytes: ClassVar[bytes | None] = None

    NON_TICKER_TOKENS: ClassVar[set[str]] = {
        "SEC", "10Q", "10K", "FY", "ANNUAL", "QUARTERLY",
    }

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
    
        if inspect.isabstract(cls):
            return

        if cls.supported_extensions is None:
            raise TypeError(
                f"{cls.__name__} must define supported_extensions, "
                'e.g. supported_extensions = [".pdf"]'
            )

        if not isinstance(cls.supported_extensions, list) or not cls.supported_extensions:
            raise TypeError(
                f"{cls.__name__}.supported_extensions must be a non-empty list[str]"
            )

        if not all(isinstance(ext, str) and ext.startswith(".") for ext in cls.supported_extensions):
            raise TypeError(
                f"{cls.__name__}.supported_extensions must contain extensions like '.pdf'"
            )

    def matches_extension(self, file_path: Path) -> bool:
        suffix = file_path.suffix.lower()
        return suffix in {ext.lower() for ext in self.supported_extensions}

    def matches_magic_bytes(self, file_path: Path) -> bool:
        if self.magic_bytes is None:
            return True

        with file_path.open("rb") as f:
            return f.read(len(self.magic_bytes)) == self.magic_bytes

    def can_parse(self, file_path: Path) -> bool:
        return self.matches_extension(file_path) and self.matches_magic_bytes(file_path)

    @abstractmethod
    def parse(self, file_path: Path) -> Document:
        raise NotImplementedError

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