from __future__ import annotations

from src.monitoring import estimate_openai_cost_usd, get_recent_monitoring_events, observe_query


def test_estimate_openai_cost_usd_handles_negative_tokens():
    cost = estimate_openai_cost_usd(
        token_usage={"prompt_tokens": -100, "completion_tokens": -200},
        input_price_per_1m=0.15,
        output_price_per_1m=0.60,
    )
    assert cost == 0


def test_observe_query_stores_recent_events():
    observe_query(
        response_time_ms=450,
        retrieved_docs=4,
        token_usage={"prompt_tokens": 100, "completion_tokens": 120, "total_tokens": 220},
        query_text="How to improve follow up quality?",
        endpoint="assistant",
        model="gpt-4o-mini",
        input_price_per_1m=0.15,
        output_price_per_1m=0.60,
    )

    payload = get_recent_monitoring_events(limit=1)
    assert payload["summary"]["request_count"] == 1
    assert payload["events"][0]["endpoint"] == "assistant"
    assert payload["events"][0]["total_tokens"] == 220
