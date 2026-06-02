from __future__ import annotations

from locust import HttpUser, between, task


def _long_trainee_answer(repeats: int = 18) -> str:
    sentence = (
        "I acknowledge the concern, confirm facts, explain next action, set timeline, "
        "and provide one accountable contact for follow-up. "
    )
    return (sentence * repeats).strip()


def _long_question(repeats: int = 8) -> str:
    base = (
        "Provide a full SOP for handling delayed delivery, repeated customer complaints, "
        "manager escalation, compensation options, and trust recovery checkpoints. "
    )
    return (base * repeats).strip()


class RagApiUser(HttpUser):
    wait_time = between(1, 3)

    @task(2)
    def health(self):
        self.client.get("/api/health", name="GET /api/health")

    @task(5)
    def assistant(self):
        payload = {"query": "How should I follow up after a test drive?", "top_k": 4}
        self.client.post("/api/assistant", json=payload, name="POST /api/assistant")

    @task(3)
    def practice_question(self):
        payload = {"topic": "delivery complaints", "difficulty": "medium", "top_k": 4}
        self.client.post("/api/practice-question", json=payload, name="POST /api/practice-question")

    @task(2)
    def evaluate(self):
        payload = {
            "question": "How to respond to delay complaint?",
            "trainee_answer": "I acknowledge concern, explain updated ETA, and offer alternatives.",
            "top_k": 4,
        }
        self.client.post("/api/evaluate", json=payload, name="POST /api/evaluate")

    @task(1)
    def mock_flow(self):
        generate_payload = {
            "topic": "post test-drive follow-up",
            "difficulty": "medium",
            "count": 3,
            "top_k": 4,
        }
        generate_res = self.client.post(
            "/api/mock/generate",
            json=generate_payload,
            name="POST /api/mock/generate",
        )
        if generate_res.status_code != 200:
            return

        questions = generate_res.json().get("questions", [])[:3]
        if not questions:
            return

        evaluate_payload = {
            "questions": questions,
            "answers": [
                "I confirm customer context and propose clear next step." for _ in questions
            ],
            "top_k": 4,
        }
        self.client.post("/api/mock/evaluate", json=evaluate_payload, name="POST /api/mock/evaluate")


class RagApiStressUser(HttpUser):
    wait_time = between(0.2, 1.0)

    @task(3)
    def assistant_stress(self):
        payload = {
            "query": _long_question(repeats=8),
            "top_k": 8,
        }
        self.client.post("/api/assistant", json=payload, name="STRESS POST /api/assistant")

    @task(3)
    def evaluate_stress(self):
        payload = {
            "question": (
                "How should a senior advisor recover trust after repeated ETA changes and still secure "
                "a positive handover experience?"
            ),
            "trainee_answer": _long_trainee_answer(repeats=18),
            "top_k": 8,
        }
        self.client.post("/api/evaluate", json=payload, name="STRESS POST /api/evaluate")

    @task(2)
    def mock_stress(self):
        generate_payload = {
            "topic": "end-to-end complaint handling and escalation",
            "difficulty": "hard",
            "count": 10,
            "top_k": 8,
        }
        generate_res = self.client.post(
            "/api/mock/generate",
            json=generate_payload,
            name="STRESS POST /api/mock/generate",
        )
        if generate_res.status_code != 200:
            return

        questions = generate_res.json().get("questions", [])[:10]
        if not questions:
            return

        evaluate_payload = {
            "questions": questions,
            "answers": [_long_trainee_answer(repeats=18) for _ in questions],
            "top_k": 8,
        }
        self.client.post("/api/mock/evaluate", json=evaluate_payload, name="STRESS POST /api/mock/evaluate")

    @task(1)
    def health(self):
        self.client.get("/api/health", name="STRESS GET /api/health")


class RagApiUltraStressUser(HttpUser):
    wait_time = between(0.05, 0.3)

    @task(5)
    def assistant_ultra(self):
        payload = {
            "query": _long_question(repeats=16),
            "top_k": 8,
        }
        self.client.post("/api/assistant", json=payload, name="ULTRA POST /api/assistant")

    @task(5)
    def evaluate_ultra(self):
        payload = {
            "question": _long_question(repeats=10),
            "trainee_answer": _long_trainee_answer(repeats=24),
            "top_k": 8,
        }
        self.client.post("/api/evaluate", json=payload, name="ULTRA POST /api/evaluate")

    @task(3)
    def mock_ultra(self):
        generate_payload = {
            "topic": (
                "enterprise-grade recovery plan for repeated delays, low NPS risk, and cross-team escalation "
                "with weekly governance review"
            ),
            "difficulty": "hard",
            "count": 10,
            "top_k": 8,
        }
        generate_res = self.client.post(
            "/api/mock/generate",
            json=generate_payload,
            name="ULTRA POST /api/mock/generate",
        )
        if generate_res.status_code != 200:
            return

        questions = generate_res.json().get("questions", [])[:10]
        if len(questions) < 10:
            questions = questions + ["Fallback stress question"] * (10 - len(questions))

        evaluate_payload = {
            "questions": questions,
            "answers": [_long_trainee_answer(repeats=24) for _ in questions],
            "top_k": 8,
        }
        self.client.post("/api/mock/evaluate", json=evaluate_payload, name="ULTRA POST /api/mock/evaluate")

    @task(1)
    def health(self):
        self.client.get("/api/health", name="ULTRA GET /api/health")
