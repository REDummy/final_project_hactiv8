from __future__ import annotations

import logging
import os
import time
from typing import Any

from flask import Flask, Response, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from src.config import get_settings
from src.logging_utils import configure_logging
from src.monitoring import (
    estimate_openai_cost_usd,
    get_recent_monitoring_events,
    init_monitoring,
    metrics_content_type,
    metrics_payload,
    observe_query,
)
from src.services.resources import load_app_resources


settings = get_settings()
configure_logging(settings.log_level, settings.app_env)
logger = logging.getLogger(__name__)

if settings.start_prometheus_http_server:
    init_monitoring(settings.prometheus_port)

if not settings.google_api_key and not settings.openai_api_key:
    raise RuntimeError("GOOGLE_API_KEY or OPENAI_API_KEY is required")

train_df, test_df, _text_col, _label_col, vectorstore, llm = load_app_resources(settings)

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")

logger.info(
    "Application initialized",
    extra={
        "app_env": settings.app_env,
        "app_version": settings.app_version,
        "train_rows": len(train_df),
        "test_rows": len(test_df),
    },
)


def quality_label(score: int) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 55:
        return "Needs Improvement"
    return "Critical"


def parse_top_k(raw_value: Any) -> int:
    try:
        top_k = int(raw_value)
    except (TypeError, ValueError):
        top_k = settings.top_k
    return max(2, min(8, top_k))


def parse_question_count(raw_value: Any) -> int:
    try:
        count = int(raw_value)
    except (TypeError, ValueError):
        count = 5
    return max(1, min(10, count))


def _estimate_cost(token_usage: dict) -> float:
    return estimate_openai_cost_usd(
        token_usage=token_usage,
        input_price_per_1m=settings.openai_input_price_per_1m,
        output_price_per_1m=settings.openai_output_price_per_1m,
    )


def build_metrics(elapsed_ms: int, token_usage: dict, retrieved_docs: int) -> dict[str, Any]:
    prompt_tokens = int(token_usage.get("prompt_tokens", 0))
    completion_tokens = int(token_usage.get("completion_tokens", 0))
    total_tokens = int(token_usage.get("total_tokens", 0))
    return {
        "response_time_ms": elapsed_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "retrieved_docs": retrieved_docs,
        "estimated_cost_usd": round(_estimate_cost(token_usage), 8),
    }


def _observe_api_usage(endpoint: str, query_text: str, elapsed_ms: int, retrieved_docs: int, token_usage: dict) -> None:
    observe_query(
        response_time_ms=elapsed_ms,
        retrieved_docs=retrieved_docs,
        token_usage=token_usage,
        query_text=query_text,
        endpoint=endpoint,
        model=settings.llm_model,
        input_price_per_1m=settings.openai_input_price_per_1m,
        output_price_per_1m=settings.openai_output_price_per_1m,
    )


def _log_api_outcome(
    endpoint: str,
    elapsed_ms: int,
    retrieved_docs: int,
    token_usage: dict,
    blocked: bool = False,
) -> None:
    logger.info(
        "API request handled",
        extra={
            "endpoint": endpoint,
            "elapsed_ms": elapsed_ms,
            "retrieved_docs": retrieved_docs,
            "prompt_tokens": int(token_usage.get("prompt_tokens", 0)),
            "completion_tokens": int(token_usage.get("completion_tokens", 0)),
            "total_tokens": int(token_usage.get("total_tokens", 0)),
            "estimated_cost_usd": round(_estimate_cost(token_usage), 8),
            "blocked": blocked,
        },
    )




@app.get("/")
def home():
    return render_template(
        "index.html",
        app_env=settings.app_env,
        app_version=settings.app_version,
        train_rows=len(train_df),
        test_rows=len(test_df),
        default_top_k=settings.top_k,
        default_mock_minutes=settings.mock_test_default_minutes,
    )
@app.get("/api/health")
def health() -> tuple[dict, int]:
    return {"status": "ok"}, 200



@app.get("/metrics")
def metrics() -> Response:
    return Response(metrics_payload(), mimetype=metrics_content_type())


@app.get("/api/monitoring/recent")
def monitoring_recent() -> Response:
    raw_limit = request.args.get("limit", "20")
    try:
        limit = int(raw_limit)
    except ValueError:
        limit = 20

    payload = get_recent_monitoring_events(limit=limit)
    payload["pricing"] = {
        "input_price_per_1m": settings.openai_input_price_per_1m,
        "output_price_per_1m": settings.openai_output_price_per_1m,
    }
    return jsonify(payload)


@app.post("/api/assistant")
def assistant_answer():
    payload = request.get_json(silent=True) or {}
    query = str(payload.get("query", "")).strip()
    if not query:
        logger.warning("Rejected empty assistant query")
        return jsonify({"error": "Question cannot be empty."}), 400

    top_k = parse_top_k(payload.get("top_k"))
    start = time.perf_counter()
    retrieved = vectorstore.similarity_search(query, k=top_k)
    contexts = [doc.page_content for doc in retrieved]
    result = llm.answer(query, contexts)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    _observe_api_usage("assistant", query, elapsed_ms, len(contexts), result["token_usage"])
    _log_api_outcome(
        "assistant",
        elapsed_ms,
        len(contexts),
        result["token_usage"],
        bool(result.get("blocked", False)),
    )

    return jsonify(
        {
            "answer": result["answer"],
            "blocked": bool(result.get("blocked", False)),
            "metrics": build_metrics(elapsed_ms, result["token_usage"], len(contexts)),
            "contexts": [
                {"content": doc.page_content, "metadata": doc.metadata or {}}
                for doc in retrieved
            ],
        }
    )


@app.post("/api/practice-question")
def practice_question():
    payload = request.get_json(silent=True) or {}
    topic = str(payload.get("topic", "")).strip()
    difficulty = str(payload.get("difficulty", "medium")).strip() or "medium"
    top_k = parse_top_k(payload.get("top_k"))

    if not topic:
        logger.warning("Rejected empty practice topic")
        return jsonify({"error": "Practice topic cannot be empty."}), 400

    start = time.perf_counter()
    retrieved = vectorstore.similarity_search(topic, k=top_k)
    contexts = [doc.page_content for doc in retrieved]
    result = llm.generate_practice_question(topic, contexts, difficulty)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    _observe_api_usage("practice-question", topic, elapsed_ms, len(contexts), result["token_usage"])
    _log_api_outcome(
        "practice-question",
        elapsed_ms,
        len(contexts),
        result["token_usage"],
        bool(result.get("blocked", False)),
    )

    return jsonify(
        {
            "question": result.get("question", ""),
            "expected_focus": result.get("expected_focus", []),
            "difficulty": result.get("difficulty", difficulty),
            "blocked": bool(result.get("blocked", False)),
            "block_reason": str(result.get("block_reason", "")),
            "metrics": build_metrics(elapsed_ms, result["token_usage"], len(contexts)),
        }
    )


@app.post("/api/evaluate")
def evaluate_answer():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()
    trainee_answer = str(payload.get("trainee_answer", "")).strip()
    top_k = parse_top_k(payload.get("top_k"))

    if not question or not trainee_answer:
        logger.warning("Rejected invalid evaluate payload")
        return jsonify({"error": "Question and trainee answer are required."}), 400

    start = time.perf_counter()
    retrieved = vectorstore.similarity_search(question, k=top_k)
    contexts = [doc.page_content for doc in retrieved]
    result = llm.evaluate_trainee_answer(
        question=question,
        trainee_answer=trainee_answer,
        contexts=contexts,
    )
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    _observe_api_usage("evaluate", question, elapsed_ms, len(contexts), result["token_usage"])
    _log_api_outcome(
        "evaluate",
        elapsed_ms,
        len(contexts),
        result["token_usage"],
        bool(result.get("blocked", False)),
    )

    report = result["evaluation"]
    overall_score = int(report.get("overall_score", 0))

    return jsonify(
        {
            "blocked": bool(result.get("blocked", False)),
            "evaluation": report,
            "quality_band": quality_label(overall_score),
            "metrics": build_metrics(elapsed_ms, result["token_usage"], len(contexts)),
            "contexts": [
                {"content": doc.page_content, "metadata": doc.metadata or {}}
                for doc in retrieved
            ],
        }
    )


@app.post("/api/mock/generate")
def mock_generate():
    payload = request.get_json(silent=True) or {}
    topic = str(payload.get("topic", "")).strip()
    difficulty = str(payload.get("difficulty", "medium")).strip() or "medium"
    count = parse_question_count(payload.get("count", 5))
    top_k = parse_top_k(payload.get("top_k"))

    if not topic:
        logger.warning("Rejected empty mock topic")
        return jsonify({"error": "Mock-test topic cannot be empty."}), 400

    start = time.perf_counter()
    retrieved = vectorstore.similarity_search(topic, k=top_k)
    contexts = [doc.page_content for doc in retrieved]
    result = llm.generate_practice_question_set(
        topic=topic,
        contexts=contexts,
        difficulty=difficulty,
        count=count,
    )
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    _observe_api_usage("mock-generate", topic, elapsed_ms, len(contexts), result["token_usage"])
    _log_api_outcome(
        "mock-generate",
        elapsed_ms,
        len(contexts),
        result["token_usage"],
        bool(result.get("blocked", False)),
    )

    return jsonify(
        {
            "questions": result.get("questions", []),
            "difficulty": difficulty,
            "blocked": bool(result.get("blocked", False)),
            "block_reason": str(result.get("block_reason", "")),
            "metrics": build_metrics(elapsed_ms, result["token_usage"], len(contexts)),
        }
    )


@app.post("/api/mock/evaluate")
def mock_evaluate():
    payload = request.get_json(silent=True) or {}
    questions = payload.get("questions", [])
    answers = payload.get("answers", [])
    top_k = parse_top_k(payload.get("top_k"))

    if not isinstance(questions, list) or not questions:
        logger.warning("Rejected empty mock questions")
        return jsonify({"error": "Questions list is required."}), 400
    if not isinstance(answers, list) or len(answers) != len(questions):
        logger.warning("Rejected mismatched mock answers")
        return jsonify({"error": "Answers list must match questions length."}), 400

    total_score = 0
    answered_count = 0
    total_eval_ms = 0
    reports: list[dict[str, Any]] = []

    for idx, question in enumerate(questions):
        q = str(question).strip()
        a = str(answers[idx]).strip()
        if not q or not a:
            continue

        start = time.perf_counter()
        retrieved = vectorstore.similarity_search(q, k=top_k)
        contexts = [doc.page_content for doc in retrieved]
        result = llm.evaluate_trainee_answer(question=q, trainee_answer=a, contexts=contexts)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        total_eval_ms += elapsed_ms

        _observe_api_usage("mock-evaluate-item", q, elapsed_ms, len(contexts), result["token_usage"])

        report = result["evaluation"]
        score = int(report.get("overall_score", 0))
        total_score += score
        answered_count += 1

        reports.append(
            {
                "index": idx + 1,
                "question": q,
                "score": score,
                "report": report,
            }
        )

    average_score = int(round(total_score / answered_count)) if answered_count else 0
    logger.info(
        "Mock evaluation completed",
        extra={
            "answered_count": answered_count,
            "average_score": average_score,
            "total_eval_ms": total_eval_ms,
        },
    )

    return jsonify(
        {
            "answered_count": answered_count,
            "average_score": average_score,
            "quality_band": quality_label(average_score),
            "total_eval_ms": total_eval_ms,
            "reports": reports,
        }
    )


def _user_facing_api_error(err: Exception) -> tuple[dict, int]:
    message = str(err).lower()
    if "api key" in message or "authentication" in message:
        return {"error": "Model provider authentication failed. Check GOOGLE_API_KEY and OPENAI_API_KEY."}, 502
    return {"error": "Internal server error."}, 500


@app.errorhandler(Exception)
def handle_exception(err: Exception):
    if isinstance(err, HTTPException):
        return err

    logger.exception("Unhandled application error", exc_info=err)
    if request.path.startswith("/api/"):
        payload, status_code = _user_facing_api_error(err)
        return jsonify(payload), status_code
    return "Internal server error.", 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8501"))
    app.run(host="0.0.0.0", port=port, debug=False)




