from __future__ import annotations


def test_health_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_assistant_rejects_empty_query(client):
    response = client.post("/api/assistant", json={"query": "   "})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_assistant_returns_answer_and_metrics(client):
    response = client.post("/api/assistant", json={"query": "How to greet customer?", "top_k": 3})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["answer"].startswith("Handled:")
    assert payload["blocked"] is False
    assert payload["metrics"]["retrieved_docs"] == 3
    assert len(payload["contexts"]) == 3


def test_practice_question_requires_topic(client):
    response = client.post("/api/practice-question", json={"topic": ""})
    assert response.status_code == 400


def test_practice_question_success(client):
    response = client.post(
        "/api/practice-question",
        json={"topic": "delivery delay", "difficulty": "easy", "top_k": 4},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["question"]
    assert payload["difficulty"] == "easy"
    assert payload["blocked"] is False


def test_evaluate_requires_payload(client):
    response = client.post("/api/evaluate", json={"question": "", "trainee_answer": ""})
    assert response.status_code == 400


def test_evaluate_returns_report(client):
    response = client.post(
        "/api/evaluate",
        json={
            "question": "How do you handle delays?",
            "trainee_answer": "I explain timeline and offer alternatives.",
            "top_k": 2,
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["quality_band"] == "Good"
    assert payload["evaluation"]["overall_score"] == 82
    assert payload["metrics"]["retrieved_docs"] == 2


def test_mock_generate_success(client):
    response = client.post(
        "/api/mock/generate",
        json={"topic": "follow up", "difficulty": "hard", "count": 4, "top_k": 3},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert len(payload["questions"]) == 4
    assert payload["difficulty"] == "hard"


def test_mock_evaluate_rejects_mismatched_lengths(client):
    response = client.post(
        "/api/mock/evaluate",
        json={"questions": ["q1", "q2"], "answers": ["a1"]},
    )
    assert response.status_code == 400


def test_mock_evaluate_success(client):
    response = client.post(
        "/api/mock/evaluate",
        json={
            "questions": ["q1", "q2", "q3"],
            "answers": ["a1", "a2", "a3"],
            "top_k": 2,
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["answered_count"] == 3
    assert payload["average_score"] == 82
    assert payload["quality_band"] == "Good"
    assert len(payload["reports"]) == 3
