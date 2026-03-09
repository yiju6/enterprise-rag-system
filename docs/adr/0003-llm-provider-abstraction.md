# ADR-0003: LLM Provider Abstraction

Date: 2026-03-07  
Status: Accepted

## Context

Different enterprises may prefer different LLM providers depending on cost, performance, or compliance constraints.

The system should support multiple providers.

## Decision

Introduce an abstraction layer for LLM providers.

Supported providers:

- OpenAI
- Anthropic

## Rationale

Benefits:

- provider flexibility
- easier benchmarking
- resilience to vendor lock-in

## Consequences

Pros:

- portable architecture
- easier experimentation

Cons:

- slightly more complex implementation