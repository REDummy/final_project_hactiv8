from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    llm_provider_mode: str = Field(default="hybrid", alias="LLM_PROVIDER_MODE")
    embedding_provider_mode: str = Field(default="hybrid", alias="EMBEDDING_PROVIDER_MODE")

    llm_model: str = Field(default="gemini-3.1-flash-lite", alias="LLM_MODEL")
    llm_fallback_model: str = Field(default="gemini-2.5-flash-lite", alias="LLM_FALLBACK_MODEL")
    llm_backup_model: str = Field(default="gpt-4.1-mini", alias="LLM_BACKUP_MODEL")
    openai_llm_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_LLM_MODEL")
    openai_llm_fallback_model: str = Field(default="gpt-4o-mini", alias="OPENAI_LLM_FALLBACK_MODEL")
    llm_timeout_seconds: int = Field(default=30, alias="LLM_TIMEOUT_SECONDS", ge=5, le=180)
    llm_max_retries: int = Field(default=2, alias="LLM_MAX_RETRIES", ge=0, le=6)
    llm_max_output_tokens: int = Field(default=700, alias="LLM_MAX_OUTPUT_TOKENS", ge=64, le=4000)

    google_embedding_model: str = Field(default="models/text-embedding-004", alias="GOOGLE_EMBEDDING_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")
    openai_input_price_per_1m: float = Field(default=0.15, alias="OPENAI_INPUT_PRICE_PER_1M", ge=0)
    openai_output_price_per_1m: float = Field(default=0.60, alias="OPENAI_OUTPUT_PRICE_PER_1M", ge=0)

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

    @property
    def use_openai_llm_only(self) -> bool:
        return (self.llm_provider_mode or "hybrid").strip().lower() == "openai"

    @property
    def use_openai_embeddings_only(self) -> bool:
        return (self.embedding_provider_mode or "hybrid").strip().lower() == "openai"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
