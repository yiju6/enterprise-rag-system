''' Retriever module for the RAG system. 
This module is responsible for retrieving relevant documents from the ChromaDB vector store based on a user's query. '''

from .config import settings
from openai import OpenAI
import chromadb

client = OpenAI(api_key=settings.openai_api_key)

def get_embeddings(query: str) -> list[float]:
    """Embed user query."""
    embeddings= client.embeddings.create(input = query, model=settings.embedding_model).data[0].embedding
    return embeddings

chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)

def retrieve(query: str) -> list[dict]:
    """Retrieve relevant documents from ChromaDB based on the user's query."""
    query_embeddings = get_embeddings(query)

    collection = chroma_client.get_collection(name="doc")

    results = collection.query(
        query_embeddings=[query_embeddings],
        n_results=settings.top_k_results,
        include=["documents", "metadatas", "ids"]
    )
    return results
