from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from .models import Document


class BaseParser(ABC):
    """Base interface for all parsers."""

    supported_extensions: ClassVar[list[str] | None] = None
    magic_bytes: ClassVar[bytes | None] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

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