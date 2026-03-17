# ADR-0005: Fixed-Size-Chunking-As-Baseline

Date: 2026-03-15
 
Status: Accepted

## Context

RecursiveTextChunker was implemented but cannot be used yet. pypdf extracts text without paragraph boundaries (\n\n), producing 1045 chunks vs 108 for fixed-size. Will be revisited in Week 3 with improved PDF parsing.

## Decision

Use `FixedSizeChunker` with chunk_size=800, overlap=150 (established in ADR-0001) as the baseline for Week 2 evaluation This ensures evaluation results reflect retrieval quality, not chunking issues.


## Consequences

Pros:
- Have a clean and reliable baseline for evaluation.


Cons:
- Fixed-size chunking may split sentences mid-way, losing semantic context
- Cannot leverage document structure (headers, paragraphs) in financial reports
- Will be replaced by structure-aware chunking in Week 3
