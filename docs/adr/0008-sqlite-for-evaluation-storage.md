# ADR-0008: sqlite for Evaluation Storage

Date: 2026-03-15 

Status: Accepted

## Context

The evaluation pipeline produces structured results that need to be persisted across runs. Two requirements drive the storage design:

1. **Regression testing (Week 5)**: comparing metrics between runs requires querying results by run_id, question_id, and metric values. CSV makes this cumbersome.

2. **Failure mode analysis**: filtering low-scoring results by metric thresholds requires flexible querying.

Options considered:
- **CSV**: simple, but no native query support. Cross-run comparison requires loading multiple files and joining in pandas.

- **PostgreSQL/MySQL**: full SQL support, but requires a running server, which overkills for a local development project.

- **SQLite**: full SQL support, zero server setup, single file, Python built-in.

## Decision

Use SQLite with two tables in a normalized schema:
```
evaluation_runs (1 row per run)
├── run_id, git_commit, config, timestamp
├── total_token_used, estimated_cost_usd, duration_seconds

evaluation_results (1 row per question per run)
├── run_id (foreign key → evaluation_runs)
├── question_id, question, answer, ground_truth
├── retrieved_docs, retrieved_chunks, source_docs
├── metrics (JSON), failure_mode (JSON), error
├── token_used, estimated_cost_usd, response_time_ms
```

The one-to-many relationship between runs and results avoids repeating run metadata (git_commit, config) for every result row.

Week 5 regression testing query example:
```sql
SELECT r1.question_id,
       r1.metrics as week2_metrics,
       r2.metrics as week4_metrics
FROM evaluation_results r1
JOIN evaluation_results r2 ON r1.question_id = r2.question_id
WHERE r1.run_id = 'week2_baseline'
AND r2.run_id = 'week4_hybrid_search'
```

## Consequences

Pros:
- Full SQL query support enables flexible failure mode analysis and regression testing
- Zero additional infrastructure: single .db file, Python built-in sqlite3
- ON DELETE CASCADE ensures referential integrity between runs and results
- Normalized schema eliminates redundant run metadata across result rows

Cons:
- Not suitable for distributed or concurrent writes; acceptable for single-user local development
- metrics and failure_mode stored as JSON strings, cannot filter by individual metric values directly in SQL (will revisit in Week 5 if needed)
- Single file, no built-in backup mechanism

## Future Work
- Week 5: add indexes on run_id and question_id for faster regression queries
- Week 6: evaluate migration to a managed database (PostgreSQL) as part of storage abstraction layer
