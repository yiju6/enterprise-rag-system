''' Extract text from various file formats, embed the text using a specified embedding model, and ingest it into the vector database.
'''

from pypdf import PdfReader
from .config import settings
from openai import OpenAI
import chromadb

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

def chunk_text(text: str) -> list[str]:
    """Chunk text into smaller pieces with specified size and overlap."""
    
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + settings.chunk_size, len(text))
        chunks.append(text[start:end])
        start += settings.chunk_size - settings.chunk_overlap

    return chunks

def get_embeddings(chunks: list[str]) -> list[list[float]]:
    """Get embeddings for each text chunk using the specified embedding model."""

    embeddings = []
    for text in chunks:
        text = text.replace("\n", " ")
        embeddings.append(client.embeddings.create(input = [text], model=settings.embedding_model).data[0].embedding)
    return embeddings

def store_in_chromadb(chunks: list[str], embeddings: list[list[float]], source: str) -> None:
    """Store the text chunks and their embeddings in ChromaDB."""

    # Create or get the collection.
    collection = chroma_client.get_or_create_collection(name="doc")

    # Add documents to the collection
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        collection.add(
            documents=[chunk],
            embeddings=[embedding],
            ids=[f"{source}_{i}"]
        )

def ingest_pdf(file_path: str) -> None:
    """Ingest a PDF file into the vector database."""

    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text)
    embeddings = get_embeddings(chunks)
    store_in_chromadb(chunks, embeddings, source=file_path)