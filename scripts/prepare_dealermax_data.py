from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI


DATASETS = {
    "glossary": "hf://datasets/DealerMax/italian-automotive-glossary/data.jsonl",
    "guides": "hf://datasets/DealerMax/italian-automotive-guides/data.jsonl",
    "faq": "hf://datasets/DealerMax/italian-automotive-faq/data.jsonl",
}

TRANSLATABLE_COLUMNS = {
    "glossary": ["category", "term", "definition", "example"],
    "guides": ["topic", "h1", "meta_description", "body_html"],
    "faq": ["category", "question", "answer"],
}



def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text



def translate_text(client: OpenAI, model: str, text: str, cache: dict[str, str]) -> str:
    if text is None:
        return ""
    text = str(text)
    if not text.strip():
        return ""

    if text in cache:
        return cache[text]

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional translator. Translate from Italian to English. "
                    "Preserve placeholders like {{DEALER_NAME}}, numbers, and formatting. "
                    "If the input contains HTML tags, preserve the HTML tags and only translate visible text. "
                    "Return only the translated text."
                ),
            },
            {"role": "user", "content": text},
        ],
    )
    translated = response.choices[0].message.content.strip()
    cache[text] = translated
    return translated



def build_corpus_rows(glossary_df: pd.DataFrame, guides_df: pd.DataFrame, faq_df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for _, r in glossary_df.iterrows():
        text = (
            f"Source: glossary\\n"
            f"Category: {r.get('category', '')}\\n"
            f"Term: {r.get('term', '')}\\n"
            f"Definition: {r.get('definition', '')}\\n"
            f"Example: {r.get('example', '')}"
        )
        rows.append({"text": text, "label": str(r.get("category", "glossary")), "source": "glossary"})

    for _, r in guides_df.iterrows():
        body_text = strip_html(str(r.get("body_html", "")))
        text = (
            f"Source: guide\\n"
            f"Topic: {r.get('topic', '')}\\n"
            f"Title: {r.get('h1', '')}\\n"
            f"Meta: {r.get('meta_description', '')}\\n"
            f"Body: {body_text}"
        )
        rows.append({"text": text, "label": str(r.get("topic", "guide")), "source": "guides"})

    for _, r in faq_df.iterrows():
        text = (
            f"Source: faq\\n"
            f"Category: {r.get('category', '')}\\n"
            f"Question: {r.get('question', '')}\\n"
            f"Answer: {r.get('answer', '')}"
        )
        rows.append({"text": text, "label": str(r.get("category", "faq")), "source": "faq"})

    return pd.DataFrame(rows)



def main() -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    if not api_key:
        raise ValueError("OPENAI_API_KEY is required in .env")

    out_dir = Path("data/translated")
    out_dir.mkdir(parents=True, exist_ok=True)

    client = OpenAI(api_key=api_key)
    cache: dict[str, str] = {}

    translated = {}

    for name, url in DATASETS.items():
        print(f"Loading {name} from {url}")
        df = pd.read_json(url, lines=True)

        for col in TRANSLATABLE_COLUMNS[name]:
            if col in df.columns:
                print(f"Translating {name}.{col} ({len(df)} rows)")
                df[col] = df[col].apply(lambda x: translate_text(client, model, str(x), cache))

        if "language" in df.columns:
            df["language"] = "en"

        out_file = out_dir / f"{name}_en.jsonl"
        df.to_json(out_file, orient="records", lines=True, force_ascii=False)
        translated[name] = df
        print(f"Saved {out_file}")

    corpus = build_corpus_rows(translated["glossary"], translated["guides"], translated["faq"])

    train_df = corpus.sample(frac=0.8, random_state=42)
    test_df = corpus.drop(train_df.index)

    train_df.to_parquet("train-00000-of-00001.parquet", index=False)
    test_df.to_parquet("test-00000-of-00001.parquet", index=False)

    summary = {
        "total_rows": int(len(corpus)),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "sources": corpus["source"].value_counts().to_dict(),
    }
    Path("data/translated/summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Done. Saved translated JSONL files and regenerated local train/test parquet.")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

