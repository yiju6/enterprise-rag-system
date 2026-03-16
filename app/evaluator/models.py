from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class EvaluationResult:
    question_id: int
    question: str
    retrieved_chunks: list[str]
    retrieved_docs: list[str]
    source_docs: str # from ground truth
    source_chunk_type: str 
    answer: str
    ground_truth: str
    metrics: dict[str, float]
    token_used: int
    estimated_cost_usd: float
    response_time_ms: float
    error: str | None
    failure_mode: list[str] | None = None

@dataclass
class EvaluationRun:
    run_id: str
    git_commit: str
    config: dict
    timestamp: str
    total_token_used: int
    estimated_cost_usd: float
    duration_seconds: float
    results: list[EvaluationResult] = field(default_factory=list)