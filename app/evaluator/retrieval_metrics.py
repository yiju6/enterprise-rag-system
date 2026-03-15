# Metrics for evaluating retrieval performance in RAG systems.

def hit_rate(retrieved_docs: list[str], source_docs: str, k: int) -> float:
    if not retrieved_docs:
        return 0.0

    pattern = source_docs.replace("*", "")
    return float(any(pattern in doc for doc in retrieved_docs[:k]))

    
def mrr(retrieved_docs: list[str], source_docs: str, k: int) -> float:
    pattern = source_docs.replace("*", "")
    for i, doc in enumerate(retrieved_docs[:k]):
        if pattern in doc:
            return 1.0 / (i + 1)
    return 0.0

def compute_retrieval_metrics(retrieved_docs: list[str], source_docs: str, k: int) -> dict[str, float]:
    return {
        'hit_rate': hit_rate(retrieved_docs, source_docs, k),
        'mrr': mrr(retrieved_docs, source_docs, k)
    }