from pathlib import Path
import json
import csv
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.evaluator.storage import get_evaluation_runs

def export_to_csv(run_id: str, output_path: str):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    runs = get_evaluation_runs()
    
    run = next((r for r in runs if r['run_id'] == run_id), None)
    if not run:
        print(f"Run {run_id} not found")
        return
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'question_id', 'question', 'source_docs', 'source_chunk_type',
            'hit_rate', 'mrr', 'context_recall',
            'faithfulness', 'answer_relevance', 'answer_correctness',
            'failure_mode', 'error',
            'token_used', 'estimated_cost_usd', 'response_time_ms',
            'answer', 'ground_truth'
        ])
        writer.writeheader()
        
        for r in run['results']:
            metrics = r['metrics'] if isinstance(r['metrics'], dict) else json.loads(r['metrics'] or '{}')
            failure_mode = r.get('failure_mode')
            if isinstance(failure_mode, str):
                failure_mode = json.loads(failure_mode or '[]')
            
            writer.writerow({
                'question_id': r['question_id'],
                'question': r['question'],
                'source_docs': r['source_docs'],
                'source_chunk_type': r.get('source_chunk_type', ''),
                'hit_rate': metrics.get('hit_rate', ''),
                'mrr': metrics.get('mrr', ''),
                'context_recall': metrics.get('context_recall', ''),
                'faithfulness': metrics.get('faithfulness', ''),
                'answer_relevance': metrics.get('answer_relevance', ''),
                'answer_correctness': metrics.get('answer_correctness', ''),
                'failure_mode': '|'.join(failure_mode) if failure_mode else '',
                'error': r.get('error', ''),
                'token_used': r.get('token_used', ''),
                'estimated_cost_usd': r.get('estimated_cost_usd', ''),
                'response_time_ms': r.get('response_time_ms', ''),
                'answer': str(r.get('answer', ''))[:200],
                'ground_truth': str(r.get('ground_truth', ''))[:200]
            })
    
    print(f"Exported {len(run['results'])} results to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_csv.py <run_id>")
        sys.exit(1)
    run_id = sys.argv[1]
    output_path = f"outputs/evaluation_runs/{run_id}/results_{run_id}.csv"
    export_to_csv(run_id=run_id, output_path=output_path)