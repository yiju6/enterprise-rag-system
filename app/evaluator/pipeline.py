import subprocess
import asyncio
from .dataset import load_dataset
from ..retriever import retrieve
from ..llm import generate_answer
from .retrieval_metrics import compute_retrieval_metrics
from .generation_metrics import compute_generation_metrics
from .models import EvaluationRun, EvaluationResult
import time
from datetime import datetime
from ..config import settings
from concurrent.futures import ThreadPoolExecutor, as_completed
from .failure_modes import classify_failure_mode


def get_git_commit() -> str:
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD']
        ).decode('utf-8').strip()
    except:
        return "unknown"

def process_row(row: dict) -> EvaluationResult:
    try:
        retrieve_results = retrieve(row["question"])
        retrieved_docs = [m["source_file"] for m in retrieve_results["metadatas"][0]]
        retrieved_contexts = retrieve_results["documents"][0]

        generation_result = generate_answer(row["question"], retrieve_results)

        retrieval_metrics = compute_retrieval_metrics(retrieved_docs, row["source_docs"], k=settings.top_k_results)
        
        loop = asyncio.new_event_loop()
        generation_metrics = loop.run_until_complete(compute_generation_metrics(
            question=row["question"],
            answer=generation_result["answer"],
            retrieved_contexts=retrieved_contexts,
            ground_truth=row["ground_truth"]
        ))
        loop.close()

        token_used = generation_result.get("token_used", 0)
        estimated_cost = token_used * 0.00002

        result = EvaluationResult(
            question_id=row["question_id"],
            question=row["question"],
            retrieved_chunks=retrieve_results["documents"][0],
            retrieved_docs=retrieved_docs,
            source_docs=row["source_docs"],
            source_chunk_type=row["source_chunk_type"], 
            answer=generation_result["answer"],
            ground_truth=row["ground_truth"],
            metrics={**retrieval_metrics, **generation_metrics},
            error=None,
            failure_mode = None,
            token_used=token_used,
            estimated_cost_usd=estimated_cost,
            response_time_ms=generation_result["response_time_ms"]
        )
        result.failure_mode = classify_failure_mode(result)
        return result

    except Exception as e:
        return EvaluationResult(
            question_id=row["question_id"],
            question=row["question"],
            retrieved_chunks=[],
            retrieved_docs=[],
            source_docs=row["source_docs"],
            source_chunk_type=row["source_chunk_type"],
            answer="",
            ground_truth=row["ground_truth"],
            metrics={},
            error=str(e),
            failure_mode=["error"],
            token_used=0,
            estimated_cost_usd=0.0,
            response_time_ms=0.0
        )

def run_evaluation(run_id: str, dataset_path: str) -> EvaluationRun:
    start_time = time.time()
    run_timestamp = datetime.utcnow().isoformat() + "Z"
    dataset = load_dataset(dataset_path)
    results = []
    total_token_used = 0
    total_estimated_cost_usd = 0.0

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_row, row) for row in dataset]
        for future in as_completed(futures):
            results.append(future.result())

    total_token_used = sum(r.token_used for r in results)
    total_estimated_cost_usd = sum(r.estimated_cost_usd for r in results)
    duration_seconds = time.time() - start_time

    return EvaluationRun(
        run_id=run_id,
        git_commit=get_git_commit(),
        config={
            "dataset_path": dataset_path,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "top_k": settings.top_k_results,
            "llm_provider": settings.llm_provider,
            "model": settings.openai_model
            },
        timestamp=run_timestamp,
        total_token_used=total_token_used,
        estimated_cost_usd=total_estimated_cost_usd,
        duration_seconds=duration_seconds,
        results=results
)