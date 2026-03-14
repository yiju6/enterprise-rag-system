''' Extract text from various file formats, embed the text using a specified embedding model, and ingest it into the vector database.
'''

from pypdf import PdfReader
from .config import settings
from openai import OpenAI
import chromadb
from .models import Chunk
from .chunker import ChunkingStrategy, FixedSizeChunker
import os
import logging


logging.getLogger("chromadb").setLevel(logging.ERROR)

client = OpenAI(api_key=settings.openai_api_key)
chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def get_embeddings(chunks: list[Chunk]) -> list[list[float]]:
    """Get embeddings for each text chunk using the specified embedding model."""

    embeddings = []
    for chunk in chunks:
        text = chunk.content.replace("\n", " ")
        embeddings.append(client.embeddings.create(input = [text], model=settings.embedding_model).data[0].embedding)
    return embeddings

def store_in_chromadb(chunks: list[Chunk], embeddings: list[list[float]]) -> None:
    """Store the text chunks and their embeddings in ChromaDB."""

    # Create or get the collection.
    collection = chroma_client.get_or_create_collection(name="doc")

    # Add documents to the collection
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        collection.add(
            documents=[chunk.content],
            embeddings=[embedding],
            ids=[f"{chunk.source_file}_{chunk.chunk_index}"],
            metadatas = [{
                "source_file": chunk.source_file, 
                "doc_type": chunk.doc_type, 
                "chunk_index": chunk.chunk_index, 
                "tenant_id": chunk.tenant_id or "", 
                "access_level": chunk.access_level or ""
                }]
        )

def ingest_pdf(file_path: str, chunker: ChunkingStrategy = None) -> None:
    if chunker is None:
        chunker = FixedSizeChunker()

    text = extract_text_from_pdf(file_path)
    chunks = chunker.chunk(text, source_file=os.path.basename(file_path), doc_type="pdf")
    embeddings = get_embeddings(chunks)
    store_in_chromadb(chunks, embeddings) 