from abc import ABC, abstractmethod
from .models import Chunk

class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, text: str, source_file: str, doc_type: str) -> list[Chunk]:
        """Chunk the input text and return a list of Chunk objects."""
        pass

class FixedSizeChunker(ChunkingStrategy):
    """Simple chunker that splits text into fixed-size chunks with overlap."""
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(self, text: str, source_file: str, doc_type: str) -> list[Chunk]:
        chunks = []
        start = 0
        index = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            chunks.append(Chunk(content=chunk_text, source_file=source_file, doc_type=doc_type, chunk_index=index, tenant_id=None, access_level=None))
            start += self.chunk_size - self.chunk_overlap
            index += 1

        return chunks



class RecursiveTextChunker(ChunkingStrategy):
    """
    Recursive text chunker that splits text hierarchically.
    Note: Requires well-structured text with paragraph boundaries (\n\n).
    Current PDF extraction (pypdf) loses document structure, producing
    single \n separators only. Switch to this chunker after improving
    PDF parsing in Week 3.
    """
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", " ", ""]
    
    def _split(self, text: str, separators: list[str]) -> list[str]:
        if not separators: # No more separators to try, return the text as a single chunk
            return [text]

        sep = separators[0]
        parts = text.split(sep)

        if len(parts) == 1:
            return self._split(text, separators[1:])
        
        chunks = []
        for part in parts:
            if len(part) <= self.chunk_size:
                chunks.append(part)
            else:
                chunks.extend(self._split(part, separators[1:]))
        
        return chunks
    
    def _add_overlap(self, chunks: list[str]) -> list[str]:
        if self.chunk_overlap == 0:
            return chunks
        
        overlapped_chunks = []
        for i in range(len(chunks)):
            chunk = chunks[i]
            if i > 0:
                overlap_start = max(0, len(chunk)-self.chunk_overlap)
                chunk = chunks[i-1][overlap_start:] + " " + chunk
            overlapped_chunks.append(chunk)
        
        return overlapped_chunks

    def chunk(self, text: str, source_file: str, doc_type: str) -> list[Chunk]:
        raw_chunks = self._split(text, self.separators)
        final_chunks = self._add_overlap(raw_chunks)
        return [Chunk(content=chunk, source_file=source_file, doc_type=doc_type, chunk_index=i, tenant_id=None, access_level=None) for i, chunk in enumerate(final_chunks)]