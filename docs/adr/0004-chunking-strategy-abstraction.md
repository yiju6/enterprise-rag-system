# ADR-0004: Chunking Strategy Abstraction

Date: 2026-03-15 

Status: Accepted

## Context

The Week 1 RAG pipeline uses a single fixed-size chunking function `chunk_text()` in `ingestor.py`. This function is hard-coded with no abstraction. 

Week 3 requires ingesting HTML and Markdown documents in addition to PDFs. 
Each format has different structure and requires different chunking approaches.
Without abstraction, adding new formats would require modifying core ingestion logic.

## Decision

Introduce a **Strategy Pattern** for chunking, with an **Abstract Base Class**  `ChunkingStrategy` defining a unified interface. Concrete implementations (`FixedSizeChunker`, `RecursiveTextChunker`) inherit from this base class.

## Consequences

Pros:
- Adding new chunking strategies in Week 3 only requires creating a new class.
- Callers (ingestor.py) are decoupled from specific implementations.
- Enables A/B testing of different chunking strategies in evaluation.

Cons:
- Slightly more complex implementation.
- RecursiveTextChunker was implemented but cannot be used yet. pypdf extracts text without paragraph boundaries (\n\n), producing 1045 chunks vs 108 for fixed-size. Will be revisited in Week 3 with improved PDF parsing.