from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_openai import ChatOpenAI


logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a Mitsubishi sales training assistant for dealership teams.
Use only the retrieved context as your source of truth.
If the context is not enough, explicitly say what is missing.
Answer in clear, practical English with SOP-style guidance.
Prioritize actionable steps, short scripts, and manager-coaching relevance.
""".strip()

DEFAULT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+the\s+above",
    r"disregard\s+.*instructions",
    r"developer\s+message",
    r"system\s+prompt",
    r"reveal\s+.*prompt",
    r"bypass\s+(security|safeguards|guardrails)",
    r"jailbreak",
    r"do\s+anything\s+now",
    r"act\s+as\s+(if\s+you\s+are\s+)?(system|developer)",
    r"<\|\s*(system|assistant|developer)\s*\|>",
]

DEFAULT_BLOCKED_WORDS = [
    "kontol",
    "memek",
    "anjing",
    "babi",
    "bangsat",
    "fuck",
    "shit",
    "bitch",
    "asshole",
]


class LlmService:
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: int,
        max_retries: int,
        max_output_tokens: int,
        fallback_model: str = "",
        enable_input_guard: bool = True,
        blocked_words: list[str] | None = None,
        injection_patterns: list[str] | None = None,
        max_input_chars: int = 3000,
    ):
        self.model_chain: list[str] = []

        primary_model = (model or "").strip()
        fallback = (fallback_model or "").strip()
        if primary_model:
            self.model_chain.append(primary_model)
        if fallback and fallback != primary_model:
            self.model_chain.append(fallback)

        self.clients = [
            ChatOpenAI(
                api_key=api_key,
                model=model_name,
                temperature=0,
                timeout=timeout_seconds,
                max_retries=max_retries,
                max_tokens=max_output_tokens,
            )
            for model_name in self.model_chain
        ]

        self.enable_input_guard = enable_input_guard
        self.max_input_chars = max_input_chars
        self.blocked_words = [w.lower() for w in (blocked_words or DEFAULT_BLOCKED_WORDS) if w and w.strip()]
        pattern_list = injection_patterns or DEFAULT_INJECTION_PATTERNS
        self.injection_regexes = [re.compile(p, re.IGNORECASE) for p in pattern_list if p.strip()]

        logger.info(
            "LLM service initialized",
            extra={
                "model_chain": self.model_chain,
                "enable_input_guard": enable_input_guard,
                "blocked_words_count": len(self.blocked_words),
                "injection_patterns_count": len(self.injection_regexes),
            },
        )

    @staticmethod
    def _token_usage(response: Any) -> dict:
        usage = getattr(response, "response_metadata", {}).get("token_usage", {})
        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }

    @staticmethod
    def _zero_usage() -> dict:
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    @staticmethod
    def _parse_json_payload(content: str) -> dict | None:
        text = content.strip()
        try:
            loaded = json.loads(text)
            return loaded if isinstance(loaded, dict) else None
        except json.JSONDecodeError:
            pass

        fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
        if fence_match:
            try:
                loaded = json.loads(fence_match.group(1))
                return loaded if isinstance(loaded, dict) else None
            except json.JSONDecodeError:
                pass

        brace_match = re.search(r"(\{[\s\S]*\})", text)
        if brace_match:
            try:
                loaded = json.loads(brace_match.group(1))
                return loaded if isinstance(loaded, dict) else None
            except json.JSONDecodeError:
                return None
        return None

    def _validate_input(self, text: str, field_name: str) -> str | None:
        if not self.enable_input_guard:
            return None

        value = (text or "").strip()
        if not value:
            return None

        if len(value) > self.max_input_chars:
            logger.warning("Input blocked by max length", extra={"field_name": field_name, "length": len(value)})
            return f"Input in '{field_name}' is too long. Maximum is {self.max_input_chars} characters."

        normalized = value.lower()
        for word in self.blocked_words:
            if re.search(rf"\b{re.escape(word)}\b", normalized):
                logger.warning("Input blocked by blocked-words policy", extra={"field_name": field_name})
                return f"Input in '{field_name}' contains blocked words based on policy."

        for pattern in self.injection_regexes:
            if pattern.search(value):
                logger.warning("Input blocked by injection pattern", extra={"field_name": field_name})
                return f"Input in '{field_name}' is flagged as a prompt-injection attempt."

        return None

    def _invoke(self, prompt: str):
        last_error: Exception | None = None

        for idx, client in enumerate(self.clients):
            model_name = self.model_chain[idx]
            try:
                if idx > 0:
                    logger.warning(
                        "Model failed; trying fallback",
                        extra={
                            "failed_model": self.model_chain[idx - 1],
                            "fallback_model": model_name,
                        },
                    )
                return client.invoke(prompt)
            except Exception as err:  # noqa: BLE001
                last_error = err
                logger.warning(
                    "Model invocation failed",
                    extra={
                        "model": model_name,
                        "attempt_index": idx + 1,
                        "error": str(err),
                    },
                )

        if last_error is not None:
            raise last_error
        raise RuntimeError("No LLM client configured")

    def answer(self, query: str, contexts: list[str]) -> dict:
        reason = self._validate_input(query, "Question")
        if reason:
            return {"answer": f"Request blocked: {reason}", "token_usage": self._zero_usage(), "blocked": True}

        context_block = "\n\n".join([f"[DOC {i+1}] {c}" for i, c in enumerate(contexts)])
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Retrieved context:\n{context_block}\n\n"
            f"User question: {query}\n"
            "Final answer:"
        )

        response = self._invoke(prompt)
        token_usage = self._token_usage(response)
        logger.debug("Assistant answer generated", extra={"contexts": len(contexts), "total_tokens": token_usage.get("total_tokens", 0)})
        return {"answer": response.content, "token_usage": token_usage, "blocked": False}

    def generate_practice_question(self, topic: str, contexts: list[str], difficulty: str) -> dict:
        reason = self._validate_input(topic, "Practice topic")
        if reason:
            return {
                "question": "",
                "expected_focus": [],
                "difficulty": difficulty,
                "token_usage": self._zero_usage(),
                "blocked": True,
                "block_reason": reason,
            }

        context_block = "\n\n".join([f"[DOC {i+1}] {c}" for i, c in enumerate(contexts)])
        prompt = (
            "You are creating one practice question for Mitsubishi sales trainees.\n"
            "Use only the retrieved context.\n"
            "Question must be in English and practical for dealership execution.\n"
            f"Difficulty: {difficulty}.\n"
            f"Topic hint from trainer: {topic}\n\n"
            f"Retrieved context:\n{context_block}\n\n"
            "Output ONLY valid JSON with shape:\n"
            '{"question":"...","expected_focus":["...","..."],"difficulty":"..."}'
        )

        response = self._invoke(prompt)
        content = str(response.content).strip()
        parsed = {"question": "", "expected_focus": [], "difficulty": difficulty}

        loaded = self._parse_json_payload(content)
        if isinstance(loaded, dict):
            parsed["question"] = str(loaded.get("question", "")).strip()
            focus = loaded.get("expected_focus", [])
            if isinstance(focus, list):
                parsed["expected_focus"] = [str(x).strip() for x in focus if str(x).strip()]
            parsed["difficulty"] = str(loaded.get("difficulty", difficulty)).strip() or difficulty
        else:
            parsed["question"] = content
            logger.warning("Practice question response was not valid JSON")

        token_usage = self._token_usage(response)
        return {
            "question": parsed["question"] or "Create a short SOP for handling delivery delay complaints.",
            "expected_focus": parsed["expected_focus"],
            "difficulty": parsed["difficulty"],
            "token_usage": token_usage,
            "blocked": False,
        }

    def generate_practice_question_set(self, topic: str, contexts: list[str], difficulty: str, count: int = 5) -> dict:
        reason = self._validate_input(topic, "Mock-test topic")
        if reason:
            return {
                "questions": [],
                "difficulty": difficulty,
                "token_usage": self._zero_usage(),
                "blocked": True,
                "block_reason": reason,
            }

        context_block = "\n\n".join([f"[DOC {i+1}] {c}" for i, c in enumerate(contexts)])
        prompt = (
            "You are creating a mini test for Mitsubishi sales trainees.\n"
            "Generate varied and practical questions.\n"
            "Use only retrieved context.\n"
            f"Topic: {topic}\n"
            f"Difficulty: {difficulty}\n"
            f"Number of questions: {count}\n"
            "Questions must be in English.\n"
            "Do NOT include answers or expected focus.\n\n"
            f"Retrieved context:\n{context_block}\n\n"
            "Output ONLY valid JSON with shape:\n"
            '{"questions":["q1","q2","q3","q4","q5"],"difficulty":"..."}'
        )

        response = self._invoke(prompt)
        content = str(response.content).strip()

        questions: list[str] = []
        loaded = self._parse_json_payload(content)
        if isinstance(loaded, dict):
            raw_questions = loaded.get("questions", [])
            if isinstance(raw_questions, list):
                questions = [str(q).strip() for q in raw_questions if str(q).strip()]

        if not questions:
            logger.warning("Practice question set response fallback used")
            questions = [f"Question {i+1}: Explain the SOP for {topic}." for i in range(count)]

        token_usage = self._token_usage(response)
        return {
            "questions": questions[:count],
            "difficulty": difficulty,
            "token_usage": token_usage,
            "blocked": False,
        }

    def evaluate_trainee_answer(self, question: str, trainee_answer: str, contexts: list[str]) -> dict:
        reason = self._validate_input(question, "Evaluation question") or self._validate_input(
            trainee_answer, "Trainee answer"
        )
        if reason:
            return {
                "evaluation": {
                    "overall_score": 0,
                    "metric_scores": {
                        "accuracy": 0,
                        "completeness": 0,
                        "sop_alignment": 0,
                        "clarity": 0,
                        "actionability": 0,
                    },
                    "strengths": [],
                    "gaps": [f"Evaluation blocked: {reason}"],
                    "improvement_tips": ["Revise the input and submit again."],
                    "reference_answer": "",
                },
                "token_usage": self._zero_usage(),
                "blocked": True,
            }

        context_block = "\n\n".join([f"[DOC {i+1}] {c}" for i, c in enumerate(contexts)])
        prompt = (
            "You are an evaluator for Mitsubishi sales trainee answers.\n"
            "Score strictly based on retrieved context only.\n"
            "Return ONLY valid JSON.\n"
            "Scoring metrics are 0-100 integers.\n"
            "Use these metrics: accuracy, completeness, sop_alignment, clarity, actionability.\n"
            "overall_score is weighted average with weights: accuracy 35%, completeness 25%, "
            "sop_alignment 20%, clarity 10%, actionability 10%.\n"
            "Output schema:\n"
            "{\n"
            '  "overall_score": 0,\n'
            '  "metric_scores": {\n'
            '    "accuracy": 0,\n'
            '    "completeness": 0,\n'
            '    "sop_alignment": 0,\n'
            '    "clarity": 0,\n'
            '    "actionability": 0\n'
            "  },\n"
            '  "strengths": ["..."],\n'
            '  "gaps": ["..."],\n'
            '  "improvement_tips": ["..."],\n'
            '  "reference_answer": "..."\n'
            "}\n\n"
            f"Question:\n{question}\n\n"
            f"Trainee answer:\n{trainee_answer}\n\n"
            f"Retrieved context:\n{context_block}"
        )

        response = self._invoke(prompt)
        content = str(response.content).strip()

        default_result = {
            "overall_score": 0,
            "metric_scores": {
                "accuracy": 0,
                "completeness": 0,
                "sop_alignment": 0,
                "clarity": 0,
                "actionability": 0,
            },
            "strengths": [],
            "gaps": ["Evaluator could not parse model output."],
            "improvement_tips": ["Try evaluating again with a clearer answer."],
            "reference_answer": "",
        }

        parsed = default_result.copy()
        loaded = self._parse_json_payload(content)
        if isinstance(loaded, dict):
            parsed["overall_score"] = int(loaded.get("overall_score", 0))
            metric_scores = loaded.get("metric_scores", {})
            if isinstance(metric_scores, dict):
                for key in parsed["metric_scores"]:
                    parsed["metric_scores"][key] = int(metric_scores.get(key, 0))
            for key in ["strengths", "gaps", "improvement_tips"]:
                value = loaded.get(key, [])
                if isinstance(value, list):
                    parsed[key] = [str(x).strip() for x in value if str(x).strip()]
            parsed["reference_answer"] = str(loaded.get("reference_answer", "")).strip()
        else:
            logger.warning("Evaluation response was not valid JSON")

        token_usage = self._token_usage(response)
        return {"evaluation": parsed, "token_usage": token_usage, "blocked": False}