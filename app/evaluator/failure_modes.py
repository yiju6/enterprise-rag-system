from .models import EvaluationResult

def classify_failure_mode(result: EvaluationResult) -> list[str]:
    if not result.metrics:
        return ["error"]
    
    modes = []
    
    if result.metrics.get('hit_rate', 0) == 0:
        modes.append("retrieval_miss")
    if result.metrics.get('context_recall', 1) < 0.5:
        modes.append("incomplete_retrieval")
    if result.metrics.get('faithfulness', 1) < 0.5:
        modes.append("hallucination")
    if result.metrics.get('answer_relevance', 1) < 0.3:
        modes.append("irrelevant_answer")
    
    return modes if modes else ["ok"]