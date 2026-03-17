# Week 2 Baseline Evaluation Results

Date: 2026-03-15

Dataset: Docugami KG-RAG, 22 questions (2023 Q3 AAPL/NVDA/MSFT, Single-Doc Single-Chunk)

Config: chunk_size=800, overlap=150, top_k=3, model=gpt-4o-mini


## Overall Metrics

| Metric | Score | Notes |
|--------|-------|-------|
| hit_rate | 1.00 | Every query retrieved the correct source document |
| mrr | 0.95 | Correct document ranked first in almost all cases |
| context_recall | 0.47 | Only 47% of required content was retrieved |
| faithfulness | 0.84 | Low hallucination rate |
| answer_relevance | 0.54 | Answers partially off-topic |
| answer_correctness | 0.54 | Significant gap vs ground truth |


## Text vs Table Breakdown

| Source Chunk Type | hit_rate | context_recall | faithfulness | answer_correctness |
|-------------------|----------|----------------|--------------|-------------------|
| Table | 1.0 | 0.476 | 0.838 | 0.598 |
| Text | 1.0 | 0.457 | 0.845 | 0.423 |

### Key Finding 1: Table answer_correctness is higher than expected (0.60 vs 0.42)

This is counterintuitive. Table questions were expected to perform worse due to 
PDF table parsing quality. Likely explanation:

- Table questions have precise numeric answers ("$83 billion") which are easier to match against ground truth

- Text questions require longer explanatory answers which are harder to match semantically

- This suggests answer_correctness favors concise, factual answers

### Key Finding 2: context_recall is equally low for both types (≈0.47)

The problem is not PDF table parsing. Both Text and Table questions suffer equally.  The root cause is **retrieval recall**, not parsing quality.



## Failure Mode Analysis

### Primary failure mode: incomplete_retrieval
```
hit_rate = 1.0  → correct document is found
context_recall = 0.47  → but not enough relevant content is retrieved
```

Root cause chain:
```
context_recall low (0.47)
  → answer built on incomplete context
  → answer_relevance low (0.54)
  → answer_correctness low (0.54)
```

### Example: Retrieval Miss on Semantic Gap

Question: "What significant changes in accounting practices were reported by NVIDIA?"

Retrieved chunks:
- "valuation of controls..." (internal controls section)
- "Information we post..." (social media disclosure)
- "UNITED STATES SECURITIES..." (cover page)

Ground truth answer references: "change in accounting estimate related to useful 
lives of property, plant, and equipment"

Analysis: the query uses "accounting practices" but the document uses "accounting 
estimate" — vector similarity fails to bridge this vocabulary gap. This is a 
classic semantic mismatch problem that hybrid search (Week 4) will address.


## Improvement Roadmap

| Week | Change | Expected Impact |
|------|--------|----------------|
| Week 3 | Improve PDF parsing, extract table structure | Improve Table chunk quality |
| Week 4 | Hybrid search (vector + keyword) | context_recall: 0.47 → 0.65+ |
| Week 4 | Query rewriting | Bridge vocabulary gaps like "accounting practices" vs "accounting estimate" |
| Week 5 | Reranking | Improve answer_relevance and answer_correctness |