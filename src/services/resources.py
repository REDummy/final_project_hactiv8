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
    logger.info("Initializing RAG indexer")
    indexer = RagIndexer(
        api_key=settings.openai_api_key,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        embedding_provider=settings.embedding_provider,
        vertex_project_id=settings.vertex_project_id,
        vertex_location=settings.vertex_location,
        vertex_embedding_model=settings.vertex_embedding_model,
    )
    vectorstore = indexer.build_vectorstore(train_df, text_col, label_col)
    logger.info("Initializing LLM service")
    llm = LlmService(
        api_key=settings.openai_api_key,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        max_output_tokens=settings.llm_max_output_tokens,
        enable_input_guard=settings.enable_input_guard,
        blocked_words=settings.blocked_words,
        injection_patterns=settings.injection_patterns,
        max_input_chars=settings.max_input_chars,
        llm_provider=settings.llm_provider,
        vertex_project_id=settings.vertex_project_id,
        vertex_location=settings.vertex_location,
    )
    logger.info("App resources ready", extra={"train_rows": len(train_df), "test_rows": len(test_df)})
    return train_df, test_df, text_col, label_col, vectorstore, llm



