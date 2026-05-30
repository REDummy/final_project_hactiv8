from __future__ import annotations

import logging
from typing import Tuple

import pandas as pd


logger = logging.getLogger(__name__)


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _build_glossary_rows(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        text = (
            f"Source: glossary\n"
            f"Category: {_safe_text(r.get('category'))}\n"
            f"Term: {_safe_text(r.get('term'))}\n"
            f"Definition: {_safe_text(r.get('definition'))}\n"
            f"Example: {_safe_text(r.get('example'))}"
        )
        rows.append({"text": text, "label": _safe_text(r.get("category")) or "glossary"})
    return rows


def _build_guides_rows(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        text = (
            f"Source: guide\n"
            f"Topic: {_safe_text(r.get('topic'))}\n"
            f"Title: {_safe_text(r.get('h1'))}\n"
            f"Meta: {_safe_text(r.get('meta_description'))}\n"
            f"Body: {_safe_text(r.get('body_html'))}"
        )
        rows.append({"text": text, "label": _safe_text(r.get("topic")) or "guides"})
    return rows


def _build_faq_rows(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        text = (
            f"Source: faq\n"
            f"Category: {_safe_text(r.get('category'))}\n"
            f"Question: {_safe_text(r.get('question'))}\n"
            f"Answer: {_safe_text(r.get('answer'))}"
        )
        rows.append({"text": text, "label": _safe_text(r.get("category")) or "faq"})
    return rows


def load_data(
    glossary_path: str,
    guides_path: str,
    faq_path: str,
) -> Tuple[pd.DataFrame, pd.DataFrame, str, str | None]:
    logger.info(
        "Loading data files",
        extra={
            "glossary_path": glossary_path,
            "guides_path": guides_path,
            "faq_path": faq_path,
        },
    )
    glossary_df = pd.read_json(glossary_path, lines=True)
    guides_df = pd.read_json(guides_path, lines=True)
    faq_df = pd.read_json(faq_path, lines=True)

    corpus_rows = []
    corpus_rows.extend(_build_glossary_rows(glossary_df))
    corpus_rows.extend(_build_guides_rows(guides_df))
    corpus_rows.extend(_build_faq_rows(faq_df))

    full_df = pd.DataFrame(corpus_rows)
    full_df["text"] = full_df["text"].astype(str).fillna("")
    full_df["label"] = full_df["label"].astype(str).fillna("unknown")

    train_df = full_df.sample(frac=0.8, random_state=42)
    test_df = full_df.drop(train_df.index)
    logger.info(
        "Data loaded",
        extra={
            "rows_total": len(full_df),
            "rows_train": len(train_df),
            "rows_test": len(test_df),
        },
    )

    return train_df, test_df, "text", "label"

