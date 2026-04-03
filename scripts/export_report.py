"""
app/evaluator/generate_report.py — Evaluation report generator

Usage:
    python app/evaluator/generate_report.py <run_id>
    python app/evaluator/generate_report.py week3_regression_v3

Outputs (under outputs/evaluation_runs/<run_id>/):
    report_<run_id>.json   — machine-readable, structured report
    report_<run_id>.md     — human-readable summary
"""

import sys
import os
import json
import statistics
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUTPUT_BASE = Path("outputs/evaluation_runs")

RETRIEVAL_METRICS = ["hit_rate", "mrr", "context_recall"]
GENERATION_METRICS = ["faithfulness", "answer_relevance", "answer_correctness"]


# ── helpers ───────────────────────────────────────────────────────────────────

def _safe_mean(values: list[float]) -> float | None:
    return round(statistics.mean(values), 4) if values else None


def _safe_median(values: list[float]) -> float | None:
    return round(statistics.median(values), 4) if values else None


def _safe_stats(values: list[float]) -> dict:
    return {
        "mean": _safe_mean(values),
        "median": _safe_median(values),
        "n": len(values),
    }


def _percentile(sorted_vals: list[float], p: float) -> float | None:
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return round(d0 + d1, 1)


def _normalize_chunk_type(raw) -> str:
    if isinstance(raw, list):
        return str(raw[0]).strip().lower() if raw else "unknown"
    if isinstance(raw, str):
        return raw.strip().lower() or "unknown"
    return "unknown"


def _normalize_failure_modes(raw) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        modes = raw
    elif isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            modes = parsed if isinstance(parsed, list) else [str(parsed)]
        except json.JSONDecodeError:
            modes = [raw]
    else:
        modes = [str(raw)]

    cleaned = []
    for m in modes:
        s = str(m).strip()
        if not s or s.lower() == "ok":
            continue
        cleaned.append(s)
    return cleaned


def _normalize_source_docs(raw) -> list[str]:
    if raw is None:
        return ["unknown"]
    if isinstance(raw, list):
        docs = raw
    elif isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return ["unknown"]
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                docs = parsed
            else:
                docs = [str(parsed)]
        except json.JSONDecodeError:
            docs = [raw]
    else:
        docs = [str(raw)]

    cleaned = [str(d).strip() for d in docs if str(d).strip()]
    return cleaned or ["unknown"]


def _collect_metric_values(results: list[dict], metric_name: str) -> list[float]:
    vals = []
    for r in results:
        metrics = r.get("metrics") or {}
        if not isinstance(metrics, dict):
            continue
        value = metrics.get(metric_name)
        if value is None:
            continue
        vals.append(value)
    return vals


def _metric_stats(results: list[dict], metric_names: list[str]) -> dict:
    out = {}
    for m in metric_names:
        out[m] = _safe_stats(_collect_metric_values(results, m))
    return out


def _split_by_chunk_type(results: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for r in results:
        ctype = _normalize_chunk_type(r.get("source_chunk_type"))
        groups.setdefault(ctype, []).append(r)
    return groups


def _fmt(val, decimals=4) -> str:
    if val is None:
        return "n/a"
    if isinstance(val, float):
        return f"{val:.{decimals}f}"
    return str(val)


def _format_mean_median_with_n(stats: dict) -> str:
    return f"{_fmt(stats.get('mean'))} / {_fmt(stats.get('median'))} (n={stats.get('n', 0)})"


# ── section builders ──────────────────────────────────────────────────────────

def build_section_metadata(run: dict, results: list[dict]) -> dict:
    return {
        "run_id": run["run_id"],
        "timestamp": run.get("timestamp"),
        "git_commit": run.get("git_commit", "unknown"),
        "config_snapshot": run.get("config") or {},
        "total_questions": len(results),
    }


def build_section_run_health(run: dict, results: list[dict]) -> dict:
    total = len(results)
    success_results = [r for r in results if not r.get("error")]
    failed_results = [r for r in results if r.get("error")]

    latencies = sorted(
        [r.get("response_time_ms") for r in success_results if r.get("response_time_ms") is not None]
    )

    total_tokens = run.get("total_token_used", 0) or 0
    total_cost = run.get("estimated_cost_usd", 0) or 0

    return {
        "total_questions": total,
        "successful_questions": len(success_results),
        "failed_questions": len(failed_results),
        "success_rate": round(len(success_results) / total, 4) if total else None,
        "latency": {
            "based_on": "success_only",
            "n": len(latencies),
            "avg_response_time_ms": round(statistics.mean(latencies), 1) if latencies else None,
            "p50_response_time_ms": round(statistics.median(latencies), 1) if latencies else None,
            "p95_response_time_ms": _percentile(latencies, 95),
        },
        "cost": {
            "based_on": "all",
            "n": total,
            "total_tokens": total_tokens,
            "avg_tokens_per_question": round(total_tokens / total, 1) if total else None,
            "total_cost_usd": round(total_cost, 6),
            "avg_cost_per_question_usd": round(total_cost / total, 6) if total else None,
        },
    }


def build_section_failure(results: list[dict]) -> dict:
    success_count = 0
    failure_count = 0
    error_count = 0
    mode_counter: dict[str, int] = {}

    for r in results:
        if r.get("error"):
            failure_count += 1
            error_count += 1
        else:
            success_count += 1

        for mode in _normalize_failure_modes(r.get("failure_mode")):
            mode_counter[mode] = mode_counter.get(mode, 0) + 1

    return {
        "summary": {
            "total_questions": len(results),
            "success_count": success_count,
            "failure_count": failure_count,
            "error_count": error_count,
        },
        "failure_mode_distribution": {
            "based_on": "all",
            "n": len(results),
            "modes": dict(sorted(mode_counter.items(), key=lambda x: (-x[1], x[0]))),
        },
    }


def _build_quality_block(results: list[dict], metric_names: list[str], based_on: str) -> dict:
    chunk_groups = _split_by_chunk_type(results)

    by_chunk_type = {}
    for ctype, cresults in sorted(chunk_groups.items(), key=lambda x: x[0]):
        by_chunk_type[ctype] = {
            "sample_count": len(cresults),
            "metrics": _metric_stats(cresults, metric_names),
        }

    return {
        "based_on": based_on,
        "overall_sample_count": len(results),
        "overall": _metric_stats(results, metric_names),
        "by_chunk_type": by_chunk_type,
    }


def build_section_core_quality(results: list[dict]) -> dict:
    return {
        "retrieval": _build_quality_block(results, RETRIEVAL_METRICS, based_on="all"),
        "generation": _build_quality_block(results, GENERATION_METRICS, based_on="all"),
    }


def build_section_distribution(results: list[dict]) -> dict:
    chunk_counter: dict[str, int] = {}
    doc_counter: dict[str, int] = {}

    for r in results:
        ctype = _normalize_chunk_type(r.get("source_chunk_type"))
        chunk_counter[ctype] = chunk_counter.get(ctype, 0) + 1

        for doc in _normalize_source_docs(r.get("source_docs")):
            doc_counter[doc] = doc_counter.get(doc, 0) + 1

    sorted_docs = dict(sorted(doc_counter.items(), key=lambda x: (-x[1], x[0])))

    return {
        "by_chunk_type": {
            "based_on": "all",
            "n": len(results),
            "counts": dict(sorted(chunk_counter.items(), key=lambda x: (-x[1], x[0]))),
        },
        "by_document": {
            "based_on": "all",
            "n": len(results),
            "total_documents": len(sorted_docs),
            "counts": sorted_docs,
        },
    }


def build_section_metric_splits(results: list[dict]) -> dict:
    success_results = [r for r in results if not r.get("error")]

    all_correctness = _collect_metric_values(results, "answer_correctness")
    success_correctness = _collect_metric_values(success_results, "answer_correctness")

    return {
        "answer_correctness": {
            "all": {
                "based_on": "all",
                **_safe_stats(all_correctness),
            },
            "success_only": {
                "based_on": "success_only",
                **_safe_stats(success_correctness),
            },
        }
    }


def build_report_json(run: dict) -> dict:
    results = run.get("results", [])

    return {
        "metadata": build_section_metadata(run, results),
        "run_health": build_section_run_health(run, results),
        "failure": build_section_failure(results),
        "core_quality": build_section_core_quality(results),
        "distribution": build_section_distribution(results),
        "metric_splits": build_section_metric_splits(results),
    }


# ── markdown formatter ────────────────────────────────────────────────────────

def _md_key_value_table(rows: list[tuple[str, str]]) -> list[str]:
    lines = ["| field | value |", "|---|---|"]
    for key, value in rows:
        lines.append(f"| {key} | {value} |")
    return lines


def _md_distribution_table(header_1: str, counts: dict[str, int]) -> list[str]:
    lines = [f"| {header_1} | count |", "|---|---|"]
    for key, value in counts.items():
        lines.append(f"| {key} | {value} |")
    return lines

def _format_mean_median(stats: dict) -> str:
    return f"{_fmt(stats.get('mean'))} / {_fmt(stats.get('median'))}"

def _md_quality_table(layer: dict, metric_names: list[str]) -> list[str]:
    chunk_types = list(layer["by_chunk_type"].keys())

    header = [f"overall (n={layer['overall_sample_count']})"]
    header.extend(
        f"{ct} (n={layer['by_chunk_type'][ct]['sample_count']})"
        for ct in chunk_types
    )

    lines = [
        "| metric | " + " | ".join(header) + " |",
        "|---|" + "|".join(["---"] * len(header)) + "|",
    ]

    for metric_name in metric_names:
        row = [metric_name]

        # overall
        row.append(_format_mean_median(layer["overall"][metric_name]))

        # by chunk type
        for ct in chunk_types:
            row.append(
                _format_mean_median(
                    layer["by_chunk_type"][ct]["metrics"][metric_name]
                )
            )

        lines.append("| " + " | ".join(row) + " |")

    return lines


def build_report_md(report: dict) -> str:
    metadata = report["metadata"]
    run_health = report["run_health"]
    failure = report["failure"]
    core_quality = report["core_quality"]
    distribution = report["distribution"]
    metric_splits = report["metric_splits"]
    cfg = metadata.get("config_snapshot", {})

    lines: list[str] = []

    # Header
    lines.append(f"# Eval report — {metadata['run_id']}")
    lines.append("")

    # Metadata
    lines.append("## Metadata")
    lines.append("")
    metadata_rows = [
        ("run_id", metadata["run_id"]),
        ("timestamp", metadata.get("timestamp") or "n/a"),
        ("git_commit", f"`{metadata.get('git_commit', 'unknown')}`"),
        ("total_questions", str(metadata["total_questions"])),
    ]
    for k, v in cfg.items():
        if v is not None:
            metadata_rows.append((k, f"`{v}`"))
    lines.extend(_md_key_value_table(metadata_rows))
    lines.append("")

    # Run Health
    lines.append("## Run Health")
    lines.append("")
    lines.extend(_md_key_value_table([
        ("total_questions", str(run_health["total_questions"])),
        ("successful_questions", str(run_health["successful_questions"])),
        ("failed_questions", str(run_health["failed_questions"])),
        ("success_rate", _fmt(run_health["success_rate"])),
    ]))
    lines.append("")

    lines.append("### Latency")
    lines.append("")
    latency = run_health["latency"]
    lines.extend(_md_key_value_table([
        ("based_on", latency["based_on"]),
        ("n", str(latency["n"])),
        ("avg_response_time_ms", _fmt(latency["avg_response_time_ms"], 1)),
        ("p50_response_time_ms", _fmt(latency["p50_response_time_ms"], 1)),
        ("p95_response_time_ms", _fmt(latency["p95_response_time_ms"], 1)),
    ]))
    lines.append("")

    lines.append("### Cost")
    lines.append("")
    cost = run_health["cost"]
    lines.extend(_md_key_value_table([
        ("based_on", cost["based_on"]),
        ("n", str(cost["n"])),
        ("total_tokens", f"{cost['total_tokens']:,}"),
        ("avg_tokens_per_question", _fmt(cost["avg_tokens_per_question"], 1)),
        ("total_cost_usd", _fmt(cost["total_cost_usd"], 6)),
        ("avg_cost_per_question_usd", _fmt(cost["avg_cost_per_question_usd"], 6)),
    ]))
    lines.append("")

    # Failure
    lines.append("## Failure")
    lines.append("")
    lines.append("### Summary")
    lines.append("")
    lines.extend(_md_key_value_table([
        ("total_questions", str(failure["summary"]["total_questions"])),
        ("success_count", str(failure["summary"]["success_count"])),
        ("failure_count", str(failure["summary"]["failure_count"])),
        ("error_count", str(failure["summary"]["error_count"])),
    ]))
    lines.append("")

    lines.append("### Failure Mode Distribution")
    lines.append("")
    lines.extend(_md_key_value_table([
        ("based_on", failure["failure_mode_distribution"]["based_on"]),
        ("n", str(failure["failure_mode_distribution"]["n"])),
    ]))
    lines.append("")
    mode_counts = failure["failure_mode_distribution"]["modes"]
    if mode_counts:
        lines.extend(_md_distribution_table("mode", mode_counts))
    else:
        lines.extend(_md_distribution_table("mode", {}))
    lines.append("")

    # Core Quality
    lines.append("## Core Quality")
    lines.append("")
    lines.append("*Columns show mean/median.")
    lines.append("")

    lines.append(f"### Retrieval (based_on={core_quality['retrieval']['based_on']})")
    lines.append("")
    lines.extend(_md_quality_table(core_quality["retrieval"], RETRIEVAL_METRICS))
    lines.append("")

    lines.append(f"### Generation (based_on={core_quality['generation']['based_on']})")
    lines.append("")
    lines.extend(_md_quality_table(core_quality["generation"], GENERATION_METRICS))
    lines.append("")

    # Distribution
    lines.append("## Distribution")
    lines.append("")

    lines.append("### By Chunk Type")
    lines.append("")
    lines.extend(_md_key_value_table([
        ("based_on", distribution["by_chunk_type"]["based_on"]),
        ("n", str(distribution["by_chunk_type"]["n"])),
    ]))
    lines.append("")
    lines.extend(_md_distribution_table("chunk_type", distribution["by_chunk_type"]["counts"]))
    lines.append("")

    lines.append("### By Document")
    lines.append("")
    lines.extend(_md_key_value_table([
        ("based_on", distribution["by_document"]["based_on"]),
        ("n", str(distribution["by_document"]["n"])),
        ("total_documents", str(distribution["by_document"]["total_documents"])),
    ]))
    lines.append("")
    lines.extend(_md_distribution_table("document", distribution["by_document"]["counts"]))
    lines.append("")

    # Metric Splits
    lines.append("## Metric Splits")
    lines.append("")

    ac_all = metric_splits["answer_correctness"]["all"]
    ac_success = metric_splits["answer_correctness"]["success_only"]

    lines.append("### Answer Correctness")
    lines.append("")
    lines.append("| group | based_on | mean / median | n |")
    lines.append("|---|---|---|---|")
    lines.append(
        f"| all | {ac_all['based_on']} | {_fmt(ac_all['mean'])} / {_fmt(ac_all['median'])} | {ac_all['n']} |"
    )
    lines.append(
        f"| success_only | {ac_success['based_on']} | {_fmt(ac_success['mean'])} / {_fmt(ac_success['median'])} | {ac_success['n']} |"
    )
    lines.append("")

    return "\n".join(lines)


# ── entry point ───────────────────────────────────────────────────────────────

def generate_report(run_id: str) -> None:
    from app.evaluator.storage import get_evaluation_runs

    runs = get_evaluation_runs()
    run = next((r for r in runs if r["run_id"] == run_id), None)
    if not run:
        print(f"Run '{run_id}' not found in database.")
        sys.exit(1)

    report = build_report_json(run)

    out_dir = OUTPUT_BASE / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"report_{run_id}.json"
    md_path = out_dir / f"report_{run_id}.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    md_content = build_report_md(report)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Report written to {out_dir}/")
    print(f"  {json_path.name}")
    print(f"  {md_path.name}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app/evaluator/generate_report.py <run_id>")
        sys.exit(1)
    generate_report(sys.argv[1])