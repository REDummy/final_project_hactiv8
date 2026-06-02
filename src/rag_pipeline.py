from __future__ import annotations

import logging
from collections.abc import Callable

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings


logger = logging.getLogger(__name__)


class FallbackEmbeddings(Embeddings):
    def __init__(self, clients: list[tuple[str, Embeddings]]):
        self.clients = clients

    def _with_fallback(self, op: str, fn: Callable[[Embeddings], list]) -> list:
        last_error: Exception | None = None
        for idx, (provider, client) in enumerate(self.clients):
            try:
                if idx > 0:
                    logger.warning("Embedding backend failed; trying fallback", extra={"fallback_provider": provider})
                return fn(client)
            except Exception as err:  # noqa: BLE001
                last_error = err
                logger.warning(
                    "Embedding operation failed",
                    extra={"provider": provider, "operation": op, "attempt_index": idx + 1, "error": str(err)},
                )

        if last_error is not None:
            raise last_error
        raise RuntimeError("No embedding backend configured")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._with_fallback("embed_documents", lambda c: c.embed_documents(texts))

    def embed_query(self, text: str) -> list[float]:
        return self._with_fallback("embed_query", lambda c: c.embed_query(text))


class RagIndexer:
    def __init__(
        self,
        google_api_key: str,
        openai_api_key: str,
        chunk_size: int,
        chunk_overlap: int,
        google_embedding_model: str = "models/text-embedding-004",
        openai_embedding_model: str = "text-embedding-3-small",
    ):
        clients: list[tuple[str, Embeddings]] = []

        if google_api_key.strip():
            clients.append(
                (
                    "google",
                    GoogleGenerativeAIEmbeddings(
                        google_api_key=google_api_key,
                        model=google_embedding_model,
                    ),
                )
            )

        if openai_api_key.strip():
            clients.append(("openai", OpenAIEmbeddings(api_key=openai_api_key, model=openai_embedding_model)))

        if not clients:
            raise RuntimeError("GOOGLE_API_KEY or OPENAI_API_KEY is required for embeddings")

        self.embeddings = FallbackEmbeddings(clients)
        self.chunker = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        logger.info(
            "Embedding backend initialized",
            extra={
                "embedding_provider_chain": [provider for provider, _ in clients],
                "google_embedding_model": google_embedding_model,
                "openai_embedding_model": openai_embedding_model,
            },
        )

    def build_vectorstore(self, train_df, text_col: str, label_col: str | None):
        docs: list[Document] = []
        for _, row in train_df.iterrows():
            text = str(row[text_col]).strip()
            if not text:
                continue

            metadata = {}
            if label_col is not None:
                metadata["label"] = str(row[label_col])
            docs.append(Document(page_content=text, metadata=metadata))

        chunked_docs = self.chunker.split_documents(docs)
        logger.info("Building FAISS vectorstore", extra={"raw_docs": len(docs), "chunked_docs": len(chunked_docs)})
        return FAISS.from_documents(chunked_docs, self.embeddings)
