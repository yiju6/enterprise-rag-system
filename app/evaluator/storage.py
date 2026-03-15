# Store Evaluation Run and Evaluation Result in the database

import sqlite3
import json
from pathlib import Path
from .models import EvaluationRun, EvaluationResult
from ..config import settings

DB_PATH = Path(getattr(settings, "evaluation_db_path", "evaluation_runs.db"))

def _get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    with _get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_runs (
                run_id TEXT PRIMARY KEY,
                git_commit TEXT,
                config TEXT,
                timestamp TEXT,
                total_token_used INTEGER,
                estimated_cost_usd REAL,
                duration_seconds REAL
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                question_id TEXT,
                question TEXT,
                retrieved_chunks TEXT,
                retrieved_docs TEXT,
                source_docs TEXT,
                answer TEXT,
                ground_truth TEXT,
                metrics TEXT,
                error TEXT,
                token_used INTEGER,
                estimated_cost_usd REAL,
                response_time_ms REAL,
                FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()

def save_evaluation_run(run: EvaluationRun) -> None:
    _init_db()
    with _get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT OR REPLACE INTO evaluation_runs
                (run_id, git_commit, config, timestamp, total_token_used, estimated_cost_usd, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.run_id,
                run.git_commit,
                json.dumps(run.config),
                run.timestamp,
                run.total_token_used,
                run.estimated_cost_usd,
                run.duration_seconds,
            ),
        )

        # remove previous results for same run if any
        c.execute("DELETE FROM evaluation_results WHERE run_id = ?", (run.run_id,))

        for result in run.results:
            # If dataclass, __dict__ works. If object, fall back to attributes.
            question_id = getattr(result, "question_id", None)
            question = getattr(result, "question", None)
            retrieved_chunks = getattr(result, "retrieved_chunks", None)
            retrieved_docs = getattr(result, "retrieved_docs", None)
            source_docs = getattr(result, "source_docs", None)
            answer = getattr(result, "answer", None)
            ground_truth = getattr(result, "ground_truth", None)
            metrics = getattr(result, "metrics", None)
            error = getattr(result, "error", None)
            token_used = getattr(result, "token_used", 0)
            estimated_cost_usd = getattr(result, "estimated_cost_usd", 0.0)
            response_time_ms = getattr(result, "response_time_ms", None)

            c.execute(
                """
                INSERT INTO evaluation_results (
                    run_id, question_id, question, retrieved_chunks, retrieved_docs, source_docs,
                    answer, ground_truth, metrics, error, token_used, estimated_cost_usd, response_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    question_id,
                    question,
                    json.dumps(retrieved_chunks),
                    json.dumps(retrieved_docs),
                    json.dumps(source_docs),
                    answer,
                    ground_truth,
                    json.dumps(metrics),
                    json.dumps(error) if error is not None else None,
                    token_used,
                    estimated_cost_usd,
                    response_time_ms,
                ),
            )
        conn.commit()

def get_evaluation_runs() -> list[dict]:
    _init_db()
    with _get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM evaluation_runs ORDER BY timestamp DESC")
        run_rows = c.fetchall()

        runs = []
        for run_row in run_rows:
            run_id = run_row["run_id"]
            c.execute("SELECT * FROM evaluation_results WHERE run_id = ? ORDER BY id", (run_id,))
            result_rows = c.fetchall()

            results = []
            for r in result_rows:
                results.append({
                    "question_id": r["question_id"],
                    "question": r["question"],
                    "retrieved_chunks": json.loads(r["retrieved_chunks"]) if r["retrieved_chunks"] else None,
                    "retrieved_docs": json.loads(r["retrieved_docs"]) if r["retrieved_docs"] else None,
                    "source_docs": json.loads(r["source_docs"]) if r["source_docs"] else None,
                    "answer": r["answer"],
                    "ground_truth": r["ground_truth"],
                    "metrics": json.loads(r["metrics"]) if r["metrics"] else None,
                    "error": json.loads(r["error"]) if r["error"] else None,
                    "token_used": r["token_used"],
                    "estimated_cost_usd": r["estimated_cost_usd"],
                    "response_time_ms": r["response_time_ms"],
                })
            runs.append({
                "run_id": run_row["run_id"],
                "git_commit": run_row["git_commit"],
                "config": json.loads(run_row["config"]) if run_row["config"] else None,
                "timestamp": run_row["timestamp"],
                "total_token_used": run_row["total_token_used"],
                "estimated_cost_usd": run_row["estimated_cost_usd"],
                "duration_seconds": run_row["duration_seconds"],
                "results": results,
            })
        return runs