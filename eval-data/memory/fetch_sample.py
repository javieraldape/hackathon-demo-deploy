#!/usr/bin/env python3
"""Fetch a small, pinned, evidence-only LongMemEval oracle sample."""

import hashlib
import json
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


REVISION = "98d7416c24c778c2fee6e6f3006e7a073259d48f"
REPOSITORY_REVISION = "9e0b455f4ef0e2ab8f2e582289761153549043fc"
DATA_URL = (
    "https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/"
    f"{REVISION}/longmemeval_oracle.json"
)
CARD_URL = (
    "https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/"
    f"{REVISION}/README.md"
)
LICENSE_URL = (
    "https://raw.githubusercontent.com/xiaowu0162/LongMemEval/"
    f"{REPOSITORY_REVISION}/LICENSE"
)
REPO = Path(__file__).resolve().parent


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "ScopedBrain-eval-data/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def write_jsonl(path, records):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source_bytes = fetch(DATA_URL)
    source = json.loads(source_bytes)
    types = sorted({row["question_type"] for row in source})
    selected = []
    selected_ids = set()
    for question_type in types:
        matches = [row for row in source if row["question_type"] == question_type and not row["question_id"].endswith("_abs")]
        for row in matches[:4]:
            selected.append(row)
            selected_ids.add(row["question_id"])
    abstentions = [row for row in source if row["question_id"].endswith("_abs")]
    for row in abstentions:
        if row["question_id"] not in selected_ids and len([x for x in selected if x["question_id"].endswith("_abs")]) < 6:
            selected.append(row)
            selected_ids.add(row["question_id"])
    selected.sort(key=lambda row: source.index(row))

    corpus, questions, labels = [], [], []
    for row in selected:
        session_ids = row["haystack_session_ids"]
        dates = row["haystack_dates"]
        sessions = []
        annotations = []
        for session_id, date, turns in zip(session_ids, dates, row["haystack_sessions"], strict=True):
            clean_turns = []
            for turn_index, turn in enumerate(turns):
                if "has_answer" in turn:
                    annotations.append({"session_id": session_id, "turn_index": turn_index, "has_answer": turn["has_answer"]})
                clean_turns.append({key: value for key, value in turn.items() if key != "has_answer"})
            sessions.append({"session_id": session_id, "date": date, "turns": clean_turns})
        corpus.append({"record_id": row["question_id"], "sessions": sessions})
        questions.append({
            "record_id": row["question_id"],
            "question_type": row["question_type"],
            "question": row["question"],
            "question_date": row.get("question_date"),
        })
        labels.append({
            "record_id": row["question_id"],
            "answer": row["answer"],
            "answer_session_ids": row.get("answer_session_ids", []),
            "has_answer_turns": annotations,
        })

    paths = {
        "corpus": REPO / "corpus.jsonl",
        "questions": REPO / "questions.jsonl",
        "labels": REPO / "labels.jsonl",
    }
    write_jsonl(paths["corpus"], corpus)
    write_jsonl(paths["questions"], questions)
    write_jsonl(paths["labels"], labels)
    (REPO / "source-card.md").write_bytes(fetch(CARD_URL))
    (REPO / "LICENSE.txt").write_bytes(fetch(LICENSE_URL))
    manifest = {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "dataset": "xiaowu0162/longmemeval-cleaned",
            "dataset_revision": REVISION,
            "file": "longmemeval_oracle.json",
            "url": DATA_URL,
            "upstream_file_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "repository": "xiaowu0162/LongMemEval",
            "repository_revision_for_license": REPOSITORY_REVISION,
            "license": "MIT (Hugging Face dataset card metadata)",
        },
        "selection": {
            "rule": "First four non-abstention records of each available question_type, plus first six abstention records, retaining source order.",
            "source_record_count": len(source),
            "selected_record_count": len(selected),
            "selected_question_types": dict(Counter(row["question_type"] for row in selected)),
            "selected_abstentions": sum(row["question_id"].endswith("_abs") for row in selected),
            "representation": "The upstream oracle records contain only answer-relevant history sessions; sessions/turns are kept in source order. Turn-level has_answer annotations are moved to labels.jsonl.",
        },
        "transformations": [
            "Separate history sessions (corpus.jsonl), prompts and question metadata (questions.jsonl), and gold answers/evidence labels (labels.jsonl).",
            "Remove turn-level has_answer from the ingestible corpus and preserve it in labels.jsonl.",
            "Represent original session IDs and dates with their unchanged turn role/content values.",
        ],
        "artifacts": {},
    }
    for name, path in paths.items():
        manifest["artifacts"][path.name] = {"sha256": digest(path), "bytes": path.stat().st_size}
    for name in ("source-card.md", "LICENSE.txt"):
        path = REPO / name
        manifest["artifacts"][name] = {"sha256": digest(path), "bytes": path.stat().st_size}
    (REPO / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Selected {len(selected)} records; corpus={paths['corpus'].stat().st_size} bytes")


if __name__ == "__main__":
    main()
