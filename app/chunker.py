# TODO Week 4: Investigate table chunking strategy for tables exceeding
# ~4000 chars. Current approach keeps tables intact which may crowd out
# other context in LLM generation. Consider row-based chunking with
# header preservation.

from __future__ import annotations

from abc import ABC, abstractmethod

from .exceptions import UnsupportedBlockTypeError
from .models import Chunk, Document

import logging
logger = logging.getLogger(__name__)


class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]:
        """Chunk a parsed document into Chunk objects."""
        raise NotImplementedError


class _FixedSizeSplitter:
    """Internal fallback splitter for long text with no usable separators."""

    def __init__(self, chunk_size: int, chunk_overlap: int):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(chunk_text)

            if end == len(text):
                break

            start += self.chunk_size - self.chunk_overlap

        return chunks


class RecursiveTextChunker:
    """
    Recursive text splitter that prefers larger semantic separators first,
    then falls back to fixed-size splitting.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", " ", ""]
        self._fallback = _FixedSizeSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def _split(self, text: str, separators: list[str]) -> list[str]:
        text = text.strip()
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        if not separators:
            return self._fallback.split_text(text)

        sep = separators[0]

        if sep == "":
            return self._fallback.split_text(text)

        parts = text.split(sep)

        if len(parts) == 1:
            return self._split(text, separators[1:])

        chunks: list[str] = []
        current = ""

        for part in parts:
            part = part.strip()
            if not part:
                continue

            candidate = part if not current else current + sep + part

            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current.strip())

                if len(part) <= self.chunk_size:
                    current = part
                else:
                    chunks.extend(self._split(part, separators[1:]))
                    current = ""

        if current:
            chunks.append(current.strip())

        return chunks

    def _add_overlap(self, chunks: list[str]) -> list[str]:
        if self.chunk_overlap == 0 or len(chunks) <= 1:
            return chunks

        overlapped_chunks: list[str] = []

        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
                continue

            prev_chunk = chunks[i - 1]
            overlap_text = prev_chunk[-self.chunk_overlap :].strip()

            if overlap_text:
                combined = f"{overlap_text} {chunk}".strip()
            else:
                combined = chunk

            overlapped_chunks.append(combined)

        return overlapped_chunks

    def split_text(self, text: str) -> list[str]:
        raw_chunks = self._split(text, self.separators)
        return self._add_overlap(raw_chunks)


class DocumentChunker(ChunkingStrategy):
    """
    Chunker for parsed documents.

    Rules:
    - text block -> RecursiveTextChunker
    - table block -> keep as a single chunk
    - Chunk.metadata = document.metadata + block.metadata
      (block metadata overwrites document metadata on key conflict)
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.text_chunker = RecursiveTextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def _merge_metadata(self, document_metadata: dict, block_metadata: dict) -> dict:
        merged = dict(document_metadata)
        merged.update(block_metadata)
        return merged

    def chunk(self, document: Document) -> list[Chunk]:
        chunks: list[Chunk] = []
        chunk_index = 0

        for block_index, block in enumerate(document.blocks):
            merged_metadata = self._merge_metadata(
                document.metadata,
                block.metadata,
            )

            if block.content_type == "table":
                if not block.content.strip():
                    continue

                chunks.append(
                    Chunk(
                        content=block.content,
                        content_type="table",
                        source_file=document.source_file,
                        doc_type=document.doc_type,
                        chunk_index=chunk_index,
                        tenant_id=None,
                        access_level=None,
                        metadata=merged_metadata,
                    )
                )
                chunk_index += 1
                continue

            if block.content_type == "text":
                text_chunks = self.text_chunker.split_text(block.content)

                for text_chunk in text_chunks:
                    if not text_chunk.strip():
                        continue

                    chunks.append(
                        Chunk(
                            content=text_chunk,
                            content_type="text",
                            source_file=document.source_file,
                            doc_type=document.doc_type,
                            chunk_index=chunk_index,
                            tenant_id=None,
                            access_level=None,
                            metadata=merged_metadata,
                        )
                    )
                    chunk_index += 1

                continue

            logger.warning(
                "Skipping unsupported block type '%s' in %s (block_index=%d)",
                block.content_type,
                document.source_file,
                block_index,
            )
        return chunks

    '''def compute_metrics(self, chunks: list[Chunk]) -> dict:
        if not chunks:
            return {
                "num_chunks": 0,
                "num_text_chunks": 0,
                "num_table_chunks": 0,
                "avg_chunk_length": 0,
                "table_ratio": 0,
            }

        num_chunks = len(chunks)
        num_text_chunks = sum(1 for c in chunks if c.content_type == "text")
        num_table_chunks = sum(1 for c in chunks if c.content_type == "table")

        total_length = sum(len(c.content) for c in chunks)
        avg_chunk_length = total_length / num_chunks

        table_ratio = num_table_chunks / num_chunks

        return {
            "num_chunks": num_chunks,
            "num_text_chunks": num_text_chunks,
            "num_table_chunks": num_table_chunks,
            "avg_chunk_length": round(avg_chunk_length, 2),
            "table_ratio": round(table_ratio, 4),
        }
'''
    def compute_metrics(self, chunks: list[Chunk]) -> dict:
        if not chunks:
            return {
                "num_chunks": 0,
                "num_text_chunks": 0,
                "num_table_chunks": 0,
                "avg_text_chunk_length": 0,
                "avg_table_chunk_length": 0,
                "table_ratio": 0,
            }

        num_chunks = len(chunks)
        text_chunks = [c for c in chunks if c.content_type == "text"]
        table_chunks = [c for c in chunks if c.content_type == "table"]

        avg_text = round(sum(len(c.content) for c in text_chunks) / len(text_chunks), 2) if text_chunks else 0
        avg_table = round(sum(len(c.content) for c in table_chunks) / len(table_chunks), 2) if table_chunks else 0

        return {
            "num_chunks": num_chunks,
            "num_text_chunks": len(text_chunks),
            "num_table_chunks": len(table_chunks),
            "avg_text_chunk_length": avg_text,
            "avg_table_chunk_length": avg_table,
            "table_ratio": round(len(table_chunks) / num_chunks, 4),
        }
        