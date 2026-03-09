# ADR-0001: Chunking Strategy

Date: 2026-03-07  
Status: Accepted

## Context

Large documents must be split into smaller chunks before embedding.

Chunk size significantly affects retrieval quality and context coherence.
- Smaller chunks improve retrieval precision but increase context fragmentation.
- Larger chunks preserve context but reduce retrieval accuracy.

## Decision

We use fixed-size chunking with:
- Chunk size: 800 characters  
- Overlap: 150 characters

## Rationale

This configuration balances:

- retrieval precision
- contextual continuity
- embedding cost

Overlap mitigates boundary fragmentation while keeping storage overhead manageable.

## Consequences

Pros:
- simple and deterministic
- good baseline for evaluation

Cons:
- may miss semantic boundaries
- redundant embeddings due to overlap

Future work may explore:
- semantic chunking
- adaptive chunk sizes
- hierarchical retrieval