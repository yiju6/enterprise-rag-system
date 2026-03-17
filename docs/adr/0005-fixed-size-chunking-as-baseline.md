# ADR-0005: Fixed-Size-Chunking-As-Baseline

Date: 2026-03-15

Status: Accepted

## Context

During Week 2, `RecursiveTextChunker` was implemented as a semantically-aware alternative to fixed-size chunking. However, testing revealed that `pypdf` extracts financial report text without paragraph boundaries (`\n\n`), causing the recursive 
splitter to fall back to line-by-line splitting on `\n`. This produced 1,045 chunks vs 108 for fixed-size chunking on the same document, a 10x increase that degrades retrieval quality.

The root cause is not the chunking algorithm, but the PDF parsing layer losing document structure. This will be addressed in Week 3 with improved PDF parsing.

## Decision

Use `FixedSizeChunker` with chunk_size=800 and overlap=150 (established in ADR-0001) as the evaluation baseline for Week 2. 

Rationale: 
- Establishing a clean baseline requires isolating one variable at a time. 
- Switching chunking strategies before fixing PDF parsing would conflate two separate issues and make evaluation results unreliable.

## Consequences

Pros:
- Produces a clean, reproducible baseline (108 chunks per document).
- Evaluation results reflect retrieval quality, not chunking artifacts.
- Enables apples-to-apples comparison when RecursiveTextChunker is introduced in Week 3.

Cons:
- Fixed-size chunking splits text at arbitrary character boundaries, potentially breaking sentences and losing semantic context.
- Cannot leverage document structure (sections, tables, paragraphs) in financial reports.
- Retrieval quality is sub-optimal until Week 3.

## Future Work
- Week 3: improve PDF parsing to preserve document structure, then switch to RecursiveTextChunker.
- Week 3: evaluate chunk quality improvement with before/after metrics comparison.