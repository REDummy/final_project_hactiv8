from __future__ import annotations

import logging

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings


logger = logging.getLogger(__name__)


class RagIndexer:
    def __init__(
        self,
        api_key: str,
        chunk_size: int,
        chunk_overlap: int,
        openai_embedding_model: str = "text-embedding-3-small",
    ):
        if not api_key.strip():
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI embeddings")

        self.embeddings = OpenAIEmbeddings(api_key=api_key, model=openai_embedding_model)
        self.chunker = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        logger.info(
            "Embedding backend initialized",
            extra={"embedding_provider": "openai", "openai_embedding_model": openai_embedding_model},
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