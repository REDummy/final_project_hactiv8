from __future__ import annotations

import logging

from src.data_loader import load_data
from src.llm_service import LlmService
from src.rag_pipeline import RagIndexer


logger = logging.getLogger(__name__)


def load_app_resources(settings):
    logger.info("Loading training corpora")
    train_df, test_df, text_col, label_col = load_data(
        settings.glossary_data_path,
        settings.guides_data_path,
        settings.faq_data_path,
    )

    llm_google_api_key = "" if settings.use_openai_llm_only else settings.google_api_key
    llm_primary_model = settings.openai_llm_model if settings.use_openai_llm_only else settings.llm_model
    llm_fallback_model = settings.openai_llm_fallback_model if settings.use_openai_llm_only else settings.llm_fallback_model
    llm_backup_model = "" if settings.use_openai_llm_only else settings.llm_backup_model

    embedding_google_api_key = "" if settings.use_openai_embeddings_only else settings.google_api_key

    logger.info(
        "Provider mode selected",
        extra={
            "llm_provider_mode": settings.llm_provider_mode,
            "embedding_provider_mode": settings.embedding_provider_mode,
            "llm_primary_model": llm_primary_model,
            "llm_fallback_model": llm_fallback_model,
            "llm_backup_model": llm_backup_model,
        },
    )

    logger.info("Initializing RAG indexer")
    indexer = RagIndexer(
        google_api_key=embedding_google_api_key,
        openai_api_key=settings.openai_api_key,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        google_embedding_model=settings.google_embedding_model,
        openai_embedding_model=settings.openai_embedding_model,
    )
    vectorstore = indexer.build_vectorstore(train_df, text_col, label_col)

    logger.info("Initializing LLM service")
    llm = LlmService(
        google_api_key=llm_google_api_key,
        openai_api_key=settings.openai_api_key,
        model=llm_primary_model,
        fallback_model=llm_fallback_model,
        backup_model=llm_backup_model,
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        max_output_tokens=settings.llm_max_output_tokens,
        enable_input_guard=settings.enable_input_guard,
        blocked_words=settings.blocked_words,
        injection_patterns=settings.injection_patterns,
        max_input_chars=settings.max_input_chars,
    )

    logger.info("App resources ready", extra={"train_rows": len(train_df), "test_rows": len(test_df)})
    return train_df, test_df, text_col, label_col, vectorstore, llm
