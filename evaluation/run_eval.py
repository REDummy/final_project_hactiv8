from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import requests


def load_cases(path: Path) -> list[dict]:
    cases = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as err:
                raise ValueError(f"Invalid JSON on line {line_no}: {err.msg}") from err
            if not isinstance(item, dict):
                raise ValueError(f"Case line {line_no} must be a JSON object")
            if not item.get("question") or not item.get("trainee_answer"):
                raise ValueError(f"Case line {line_no} must contain 'question' and 'trainee_answer'")
            item.setdefault("min_score", 60)
            cases.append(item)
    if not cases:
        raise ValueError("No evaluation cases loaded")
    return cases


def run_case(base_url: str, case: dict, top_k: int, timeout: float) -> dict:
    started = time.perf_counter()
    response = requests.post(
        f"{base_url}/api/evaluate",
        json={
            "question": case["question"],
            "trainee_answer": case["trainee_answer"],
            "top_k": top_k,
        },
        timeout=timeout,
    )
    latency_ms = int((time.perf_counter() - started) * 1000)

    if response.status_code != 200:
        return {
            "question": case["question"],
            "status_code": response.status_code,
            "passed": False,
            "score": 0,
            "latency_ms": latency_ms,
            "error": response.text,
        }

    payload = response.json()
    score = int(payload.get("evaluation", {}).get("overall_score", 0))
    min_score = int(case.get("min_score", 60))
    blocked = bool(payload.get("blocked", False))

    return {
        "question": case["question"],
        "status_code": 200,
        "passed": (score >= min_score) and not blocked,
        "score": score,
        "min_score": min_score,
        "quality_band": payload.get("quality_band", "Unknown"),
        "latency_ms": latency_ms,
        "blocked": blocked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run API evaluation cases against /api/evaluate")
    parser.add_argument("--base-url", default="http://localhost:8501")
    parser.add_argument("--cases", default="evaluation/eval_cases.jsonl")
    parser.add_argument("--output", default="evaluation/reports/latest.json")
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--min-pass-rate", type=float, default=0.8)
    args = parser.parse_args()

    cases = load_cases(Path(args.cases))
    results = [run_case(args.base_url.rstrip("/"), case, args.top_k, args.timeout) for case in cases]

    passed = sum(1 for item in results if item["passed"])
    scores = [item["score"] for item in results]
    latencies = [item["latency_ms"] for item in results]

    summary = {
        "base_url": args.base_url,
        "cases": len(results),
        "pass_count": passed,
        "pass_rate": round(passed / len(results), 4),
        "avg_score": round(statistics.mean(scores), 2),
        "avg_latency_ms": round(statistics.mean(latencies), 2),
        "max_latency_ms": max(latencies),
        "min_pass_rate_required": args.min_pass_rate,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"summary": summary, "results": results}, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))
    return 0 if summary["pass_rate"] >= args.min_pass_rate else 1


if __name__ == "__main__":
    sys.exit(main())
