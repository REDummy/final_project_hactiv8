from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass

import pandas as pd
import pytest


@dataclass
class DummyDoc:
    page_content: str
    metadata: dict


class DummyVectorStore:
    def similarity_search(self, query: str, k: int = 4):
        return [
            DummyDoc(page_content=f"context-{idx + 1} for {query}", metadata={"rank": idx + 1})
            for idx in range(k)
        ]


class DummyLlm:
    def answer(self, query: str, contexts: list[str]) -> dict:
        return {
            "answer": f"Handled: {query}",
            "token_usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
            "blocked": False,
        }

    def generate_practice_question(self, topic: str, contexts: list[str], difficulty: str) -> dict:
        return {
            "question": f"How do you handle {topic}?",
            "expected_focus": ["SOP", "Customer empathy"],
            "difficulty": difficulty,
            "token_usage": {"prompt_tokens": 10, "completion_tokens": 14, "total_tokens": 24},
            "blocked": False,
            "block_reason": "",
        }

    def generate_practice_question_set(self, topic: str, contexts: list[str], difficulty: str, count: int = 5) -> dict:
        return {
            "questions": [f"Question {idx + 1} about {topic}" for idx in range(count)],
            "difficulty": difficulty,
            "token_usage": {"prompt_tokens": 30, "completion_tokens": 40, "total_tokens": 70},
            "blocked": False,
            "block_reason": "",
        }

    def evaluate_trainee_answer(self, question: str, trainee_answer: str, contexts: list[str]) -> dict:
        return {
            "evaluation": {
                "overall_score": 82,
                "metric_scores": {
                    "accuracy": 85,
                    "completeness": 80,
                    "sop_alignment": 81,
                    "clarity": 82,
                    "actionability": 83,
                },
                "strengths": ["Clear SOP flow"],
                "gaps": ["Could include timeline details"],
                "improvement_tips": ["Add exact escalation timing"],
                "reference_answer": "Follow SOP A-B-C.",
            },
            "token_usage": {"prompt_tokens": 45, "completion_tokens": 60, "total_tokens": 105},
            "blocked": False,
        }


def _fake_load_app_resources(_settings):
    train_df = pd.DataFrame([{"text": "train", "label": "faq"}])
    test_df = pd.DataFrame([{"text": "test", "label": "guides"}])
    return train_df, test_df, "text", "label", DummyVectorStore(), DummyLlm()


@pytest.fixture()
def app_module(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("START_PROMETHEUS_HTTP_SERVER", "false")

    import src.services.resources as resources

    monkeypatch.setattr(resources, "load_app_resources", _fake_load_app_resources)

    if "app" in sys.modules:
        del sys.modules["app"]

    module = importlib.import_module("app")
    return module


@pytest.fixture()
def client(app_module):
    return app_module.app.test_client()

