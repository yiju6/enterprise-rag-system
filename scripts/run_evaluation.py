import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.evaluator.pipeline import run_evaluation
from app.evaluator.storage import save_evaluation_run

run = run_evaluation(
    run_id="week2_baseline",
    dataset_path="data/evaluation/qna_data.csv"
    companies=["AAPL", "NVDA", "MSFT"],
    quarter="2023 Q3"
)
save_evaluation_run(run)
print(f"Done. {len(run.results)} questions evaluated.")
print(f"Total tokens: {run.total_token_used}")
print(f"Duration: {run.duration_seconds:.1f}s")