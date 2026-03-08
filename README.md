# enterprise-rag-system
KnowledgeDesk is a prototype enterprise internal knowledge base system. It enables employees to upload company documents and ask questions in natural language, receiving accurate answers with source citations — eliminating the need to manually search through files.

## Features

- **PDF Ingestion** — Upload and index company documents automatically
- **Semantic Search** — Retrieve relevant content using vector similarity search (ChromaDB)
- **Q&A with Citations** - Get answers with source references to specific document chunks
- **REST API** — FastAPI backend with `/ingest` and `/ask` endpoints
- **Multi-LLM Support** - Compatible with OpenAI and Anthropic
- **Web UI** — Simple chat interface built with Streamlit

## Tech Stack

- **Backend** - Python, FastAPI
- **Vector Database** — ChromaDB
- **Embeddings** — text-embedding-3-small
- **LLM** — OpenAI/Anthropic
- **Frontend** — Streamlit