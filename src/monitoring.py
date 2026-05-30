from __future__ import annotations

import logging

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest, start_http_server


logger = logging.getLogger(__name__)
_monitoring_started = False

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


def observe_query(response_time_ms: int, retrieved_docs: int, token_usage: dict) -> None:
    REQUEST_COUNT.inc()
    REQUEST_LATENCY_SECONDS.observe(max(response_time_ms, 0) / 1000)
    RETRIEVED_DOCS.observe(max(retrieved_docs, 0))
    LAST_RESPONSE_TIME_MS.set(max(response_time_ms, 0))

    prompt_tokens = int(token_usage.get("prompt_tokens", 0))
    completion_tokens = int(token_usage.get("completion_tokens", 0))
    total_tokens = int(token_usage.get("total_tokens", 0))

    if prompt_tokens > 0:
        PROMPT_TOKENS.inc(prompt_tokens)
    if completion_tokens > 0:
        COMPLETION_TOKENS.inc(completion_tokens)
    if total_tokens > 0:
        TOTAL_TOKENS.inc(total_tokens)
