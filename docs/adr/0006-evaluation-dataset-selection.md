# ADR-0006: Evaluation Dataset Selection

Date: 2026-03-15 

Status: Accepted

## Context

A reliable evaluation dataset is foundational to the entire 10-week project. Every retrieval and generation improvement needs to be measured against a consistent ground truth. The dataset must satisfy five criteria:

1. Questions with unambiguous, verifiable answers
2. Human-reviewed ground truth (not LLM-generated without review)
3. Realistic enterprise documents (not toy examples)
4. Difficulty stratification to support progressive evaluation across weeks
5. Format diversity to support Week 3 multi-source ingestion

Several options were considered:

- **HuggingFace RAG datasets**: questions are tied to their own document corpus, not compatible with our vector store
- **GitLab Employee Handbook**: real HR documents, but answers are ambiguous and policies change frequently — hard to define ground truth
- **LLM-generated synthetic data**: fast to create, but "self-grading" risk makes evaluation unreliable
- **Docugami KG-RAG dataset**: 20 real financial reports (10-Q filings) from AAPL, AMZN, INTC, MSFT, NVDA with 195 human-reviewed QA pairs

## Decision

Use the **Docugami KG-RAG dataset** as the primary evaluation dataset for the 10-week project.

The dataset is stratified by difficulty:
- **Single-Doc Single-Chunk RAG** (76 questions) — Week 2-3 baseline
- **Single-Doc Multi-Chunk RAG** (54 questions) — Week 4-5 after retrieval improvements
- **Multi-Doc RAG** (65 questions) — Week 4 + after hybrid search

Week 2 uses only the 76 Single-Doc Single-Chunk questions, further filtered to 3 companies (AAPL, NVDA, MSFT) and 2023 Q3 filings (22 questions) matching the ingested documents.

## Consequences

Pros:
- 195 human-reviewed QA pairs with source document annotations — high-quality ground truth.
- Difficulty stratification maps directly to the 10-week improvement roadmap.
- 5 companies × multiple quarters = natural multi-tenant simulation for Week 7.
- Questions cover both Text and Table chunk types, enabling failure mode analysis.

Cons:
- All 20 documents are PDF - Week 3 requires HTML and Markdown formats.
- Financial reports are public data — no PII present for Week 8 safety testing.
- Dataset covers 2022-2023 filings only — cannot test with more recent data.

## Future Work
- Week 3: download HTML versions of the same filings from SEC EDGAR to support multi-format ingestion without changing the question set.
- Week 4: expand evaluation to Multi-Chunk and Multi-Doc questions as retrieval improves.
- Week 7: use different companies as separate tenants to test isolation.
- Week 8: manually create 5-10 PII test cases to supplement the dataset.