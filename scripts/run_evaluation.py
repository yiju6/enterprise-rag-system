import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.evaluator.pipeline import run_evaluation
from app.evaluator.storage import save_evaluation_run

if len(sys.argv) < 2:
    print("Usage: python run_evaluation.py <run_id>")
    sys.exit(1)

run_id = sys.argv[1]

run = run_evaluation(
    run_id=run_id,
    dataset_path="data/evaluation/qna_data.csv",
    companies=["AAPL", "NVDA", "MSFT"],
    quarter="2023 Q3"
)
save_evaluation_run(run)
print(f"Done. {len(run.results)} questions evaluated.")
print(f"Total tokens: {run.total_token_used}")
print(f"Duration: {run.duration_seconds:.1f}s")