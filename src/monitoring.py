from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from threading import Lock

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest, start_http_server


logger = logging.getLogger(__name__)
_monitoring_started = False
_recent_lock = Lock()
_recent_events: deque[dict] = deque(maxlen=200)

REQUEST_COUNT = Counter(
    "rag_requests_total",
    "Total number of user queries handled by the RAG app",
)

REQUEST_LATENCY_SECONDS = Histogram(
    "rag_request_latency_seconds",
    "End-to-end latency per query",
    buckets=(0.2, 0.5, 1, 2, 3, 5, 8, 13, 21),
)

PROMPT_TOKENS = Counter(
    "rag_prompt_tokens_total",
    "Total prompt tokens consumed",
)

COMPLETION_TOKENS = Counter(
    "rag_completion_tokens_total",
    "Total completion tokens consumed",
)

TOTAL_TOKENS = Counter(
    "rag_total_tokens_total",
    "Total tokens consumed",
)

ESTIMATED_COST_USD = Counter(
    "rag_estimated_openai_cost_usd_total",
    "Estimated OpenAI usage cost in USD",
)

RETRIEVED_DOCS = Histogram(
    "rag_retrieved_docs_per_query",
    "Retrieved documents count per query",
    buckets=(1, 2, 3, 4, 5, 8, 13),
)

LAST_RESPONSE_TIME_MS = Gauge(
    "rag_last_response_time_ms",
    "Last query response time in milliseconds",
)


def init_monitoring(port: int) -> None:
    global _monitoring_started
    if _monitoring_started:
        logger.debug("Prometheus server already started")
        return
    start_http_server(port)
    _monitoring_started = True
    logger.info("Prometheus exporter started", extra={"port": port})


def metrics_payload() -> bytes:
    return generate_latest()


def metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST


def estimate_openai_cost_usd(
    token_usage: dict,
    input_price_per_1m: float,
    output_price_per_1m: float,
) -> float:
    prompt_tokens = max(int(token_usage.get("prompt_tokens", 0)), 0)
    completion_tokens = max(int(token_usage.get("completion_tokens", 0)), 0)

    input_cost = (prompt_tokens / 1_000_000) * max(float(input_price_per_1m), 0.0)
    output_cost = (completion_tokens / 1_000_000) * max(float(output_price_per_1m), 0.0)
    return input_cost + output_cost


def observe_query(
    response_time_ms: int,
    retrieved_docs: int,
    token_usage: dict,
    query_text: str,
    endpoint: str,
    model: str,
    input_price_per_1m: float,
    output_price_per_1m: float,
) -> None:
    REQUEST_COUNT.inc()
    REQUEST_LATENCY_SECONDS.observe(max(response_time_ms, 0) / 1000)
    RETRIEVED_DOCS.observe(max(retrieved_docs, 0))
    LAST_RESPONSE_TIME_MS.set(max(response_time_ms, 0))

    prompt_tokens = max(int(token_usage.get("prompt_tokens", 0)), 0)
    completion_tokens = max(int(token_usage.get("completion_tokens", 0)), 0)
    total_tokens = max(int(token_usage.get("total_tokens", 0)), 0)
    estimated_cost_usd = estimate_openai_cost_usd(token_usage, input_price_per_1m, output_price_per_1m)

    if prompt_tokens > 0:
        PROMPT_TOKENS.inc(prompt_tokens)
    if completion_tokens > 0:
        COMPLETION_TOKENS.inc(completion_tokens)
    if total_tokens > 0:
        TOTAL_TOKENS.inc(total_tokens)
    if estimated_cost_usd > 0:
        ESTIMATED_COST_USD.inc(estimated_cost_usd)

    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "model": model,
        "query": (query_text or "").strip(),
        "response_time_ms": max(response_time_ms, 0),
        "retrieved_docs": max(retrieved_docs, 0),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(estimated_cost_usd, 8),
    }
    with _recent_lock:
        _recent_events.appendleft(event)


def get_recent_monitoring_events(limit: int = 20) -> dict:
    safe_limit = max(1, min(int(limit), 100))

    with _recent_lock:
        events = list(_recent_events)[:safe_limit]

    summary = {
        "request_count": len(events),
        "prompt_tokens": sum(int(e.get("prompt_tokens", 0)) for e in events),
        "completion_tokens": sum(int(e.get("completion_tokens", 0)) for e in events),
        "total_tokens": sum(int(e.get("total_tokens", 0)) for e in events),
        "estimated_cost_usd": round(sum(float(e.get("estimated_cost_usd", 0.0)) for e in events), 8),
    }
    return {"events": events, "summary": summary}