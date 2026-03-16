# ADR-0005: Fixed-Size-Chunking-As-Baseline

Date: 2026-03-15 
Status: Accepted

    决定：Week 2 用 FixedSizeChunker 而不是 RecursiveTextChunker
    原因：pypdf 丢失文档结构，recursive chunking 产生1045个碎片
    trade-off：检索质量次优，但 baseline 干净可信
    改进方向：Week 3 改进 PDF 解析后切换

## Context

Different enterprises may prefer different LLM providers depending on cost, performance, or compliance constraints.

The system should support multiple providers.

## Decision

Introduce an abstraction layer for LLM providers.


## Rationale

Benefits:


## Consequences

Pros:


Cons:
