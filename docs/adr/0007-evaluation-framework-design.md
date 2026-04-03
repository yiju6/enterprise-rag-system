# ADR-0007: Evaluation Framework Design

Date: 2026-03-15

Status: Accepted

## Context

Production RAG systems require continuous, measurable evaluation. Without a structured evaluation framework, it is impossible to know whether system changes improve or degrade quality.

Week 2 establishes an offline evaluation pipeline: run the system against a fixed dataset, compute metrics, and store results for regression testing in future weeks.

Three categories of evaluation exist:
- **Deterministic metrics**: rule-based, no LLM required, fully reproducible
- **LLM-as-Judge**: uses an LLM to assess semantic quality， necessary when string matching is insufficient
- **Human evaluation**: the Docugami dataset provides human-reviewed ground truth answers, used directly as reference

## Decision

**Retrieval layer - Deterministic metrics:**
- `Hit Rate@K`: whether the correct source document appears in the top-K results
- `MRR (Mean Reciprocal Rank)`: rank position of the correct document
- `Context Recall`: measures how many of the relevant documents (or pieces of information) were successfully retrieved.

These are suitable because the Docugami dataset provides `source_docs` annotations, enabling direct document-level matching without LLM involvement.

**Generation layer - LLM-as-Judge via RAGAS:**
- `Faithfulness`: whether the answer is grounded in retrieved context (1 - hallucination rate)
- `Answer Relevance`: whether the answer addresses the question
- `Answer Correctness`: semantic similarity to ground truth

RAGAS is used rather than a custom implementation because the team has invested significant effort refining the prompts and logic behind these metrics. The marginal value of reimplementing them is low.

**Metrics explicitly excluded:**
- `EM/F1`: financial report questions are mostly explanatory, not exact-match. RAGAS Answer Correctness covers semantic correctness more effectively.
- `Context Precision`: measures retrieval noise, but without reranking (Week 5), noise will be consistently high. Establishing this baseline now has no comparative value until Week 5.

**System-level metrics:** token usage and latency are tracked per question and per evaluation run to support cost optimization in Week 10.

## Consequences

Pros:
- Deterministic metrics are fast, cheap, and fully reproducible
- LLM-as-Judge captures semantic quality that string matching cannot
- Three-layer design (Deterministic/LLM-as-Judge/Human Eval) provides cross-validation. If deterministic and LLM metrics agree, confidence is higher.
- SQLite storage enables SQL-based regression testing in Week 5

Cons:
- RAGAS metrics depend on LLM judgment, introducing model-version inconsistency. Mitigated by pinning model version (`gpt-4o-mini-2024-07-18`) and setting `temperature=0`
- LLM-as-Judge has higher cost and latency. 22 questions took ~400 seconds.
- asyncio + ThreadPoolExecutor interaction required careful handling; each thread creates its own event loop via `asyncio.new_event_loop()`

## Future Work
- Week 5: add Context Precision after reranking is introduced
- Week 5: implement regression testing using stored SQLite results
- Week 8: add latency and token usage dashboards via observability tooling
- Week 10: use token usage history for cost optimization analysis