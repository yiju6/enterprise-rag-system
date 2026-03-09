# ADR-0002: Vector Store Selection

Date: 2026-03-07  
Status: Accepted

## Context

The RAG system requires a vector database to store document embeddings and perform similarity search.

Several options exist:

- ChromaDB
- Pinecone
- Weaviate
- pgvector

## Decision

Use **ChromaDB** for the prototype.

## Rationale

ChromaDB offers:

- lightweight local setup
- no external infrastructure
- simple Python integration

This is suitable for early development and experimentation.

## Consequences

Pros:

- fast local iteration
- easy development setup

Cons:

- limited horizontal scalability
- not optimized for large production workloads

Future versions may migrate to:

- pgvector
- Pinecone
- other managed vector databases