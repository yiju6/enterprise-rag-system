''' 
Extract text from various file formats, embed the text using a specified embedding model, and ingest it into the vector database.
'''

from .config import settings
from openai import OpenAI
import chromadb
from .models import Chunk
from .chunker import DocumentChunker
import logging
from .parser_router import ParserRouter
from .pdf_parser import PDFParser
from pathlib import Path

logging.getLogger("chromadb").setLevel(logging.ERROR)

client = OpenAI(api_key=settings.openai_api_key)
chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)

# Default shared instances for production usage.
default_router = ParserRouter(parsers=[PDFParser()])
default_chunker = DocumentChunker()

def get_embeddings(chunks: list[Chunk]) -> list[list[float]]:
    """Get embeddings for each text chunk using the specified embedding model."""

    embeddings = []
    for chunk in chunks:
        text = chunk.content.replace("\n", " ")
        embeddings.append(client.embeddings.create(input = [text], model=settings.embedding_model).data[0].embedding)
    return embeddings

def _clean_chroma_metadata(metadata: dict) -> dict:
    """
    ChromaDB metadata only supports str | int | float | bool.
    Drop None and stringify unsupported values defensively.
    """
    cleaned = {}

    for key, value in metadata.items():
        if value is None:
            continue

        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        else:
            cleaned[key] = str(value)

    return cleaned

def store_in_chromadb(chunks: list[Chunk], embeddings: list[list[float]]) -> None:
    """Store the text chunks and their embeddings in ChromaDB."""

    # Create or get the collection.
    collection = chroma_client.get_or_create_collection(name="doc")

    for chunk, embedding in zip(chunks, embeddings):
        metadata = _clean_chroma_metadata(
            {
                "content_type": chunk.content_type,
                "source_file": chunk.source_file,
                "doc_type": chunk.doc_type,
                "chunk_index": chunk.chunk_index,
                "tenant_id": chunk.tenant_id or "",
                "access_level": chunk.access_level or "",
                **chunk.metadata,
            }
        )

        collection.add(
            documents=[chunk.content],
            embeddings=[embedding],
            ids=[f"{chunk.source_file}_{chunk.chunk_index}"],
            metadatas=[metadata],
        )


def ingest(file_path: Path, router: ParserRouter = default_router,
    chunker: DocumentChunker = default_chunker,) -> None:
    """
    End-to-end ingestion pipeline:
    ParserRouter.parse(file_path) -> DocumentChunker.chunk(document)
    -> embeddings -> ChromaDB
    """
    document = router.parse(file_path)
    chunks = chunker.chunk(document)
    embeddings = get_embeddings(chunks)
    store_in_chromadb(chunks, embeddings)
