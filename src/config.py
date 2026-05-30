from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    llm_model: str = Field(default="claude-haiku-4-5", alias="LLM_MODEL")
    llm_timeout_seconds: int = Field(default=30, alias="LLM_TIMEOUT_SECONDS", ge=5, le=180)
    llm_max_retries: int = Field(default=2, alias="LLM_MAX_RETRIES", ge=0, le=6)
    llm_max_output_tokens: int = Field(default=700, alias="LLM_MAX_OUTPUT_TOKENS", ge=64, le=4000)

    llm_provider: str = Field(default="vertex_claude", alias="LLM_PROVIDER")
    embedding_provider: str = Field(default="vertex", alias="EMBEDDING_PROVIDER")

    vertex_project_id: str = Field(default="", alias="VERTEX_PROJECT_ID")
    vertex_location: str = Field(default="us-central1", alias="VERTEX_LOCATION")
    vertex_embedding_model: str = Field(default="text-embedding-005", alias="VERTEX_EMBEDDING_MODEL")

    glossary_data_path: str = Field(default="data/glossary_en.jsonl", alias="GLOSSARY_DATA_PATH")
    guides_data_path: str = Field(default="data/guides_en.jsonl", alias="GUIDES_DATA_PATH")
    faq_data_path: str = Field(default="data/faq_en.jsonl", alias="FAQ_DATA_PATH")

    top_k: int = Field(default=4, alias="TOP_K", ge=1, le=12)
    chunk_size: int = Field(default=600, alias="CHUNK_SIZE", ge=200, le=3000)
    chunk_overlap: int = Field(default=100, alias="CHUNK_OVERLAP", ge=0, le=1000)

    prometheus_port: int = Field(default=8000, alias="PROMETHEUS_PORT", ge=1024, le=65535)
    start_prometheus_http_server: bool = Field(default=True, alias="START_PROMETHEUS_HTTP_SERVER")

    app_env: str = Field(default="dev", alias="APP_ENV")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    enable_input_guard: bool = Field(default=True, alias="ENABLE_INPUT_GUARD")
    max_input_chars: int = Field(default=3000, alias="MAX_INPUT_CHARS", ge=200, le=10000)
    blocked_words_csv: str = Field(default="", alias="BLOCKED_WORDS")
    injection_patterns_csv: str = Field(default="", alias="INJECTION_PATTERNS")

    mock_test_default_minutes: int = Field(default=15, alias="MOCK_TEST_DEFAULT_MINUTES", ge=3, le=60)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def blocked_words(self) -> list[str]:
        return [w.strip() for w in self.blocked_words_csv.split(",") if w.strip()]

    @property
    def injection_patterns(self) -> list[str]:
        return [p.strip() for p in self.injection_patterns_csv.split(",") if p.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
