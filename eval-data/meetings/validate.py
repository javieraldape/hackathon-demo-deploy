#!/usr/bin/env python3
"""Validate sampled meeting transcription and span/answer separation."""

import hashlib
import json
from pathlib import Path


root = Path(__file__).resolve().parent
manifest = json.loads((root / "manifest.json").read_text())
assert len(manifest["raw_sha256"]) == 3
turns = queries = 0
for name, expected in manifest["raw_sha256"].items():
    corpus_path = root / "corpus" / f"{name}.json"
    labels_path = root / "labels" / f"{name}.json"
    corpus = json.loads(corpus_path.read_text())
    labels = json.loads(labels_path.read_text())
    assert hashlib.sha256(corpus_path.read_bytes()).hexdigest() == manifest["corpus_sha256"][name]
    assert hashlib.sha256(labels_path.read_bytes()).hexdigest() == manifest["labels_sha256"][name]
    assert list(corpus) == ["meeting_transcripts"] and "meeting_transcripts" not in labels
    assert all(set(turn) == {"speaker", "content"} for turn in corpus["meeting_transcripts"])
    size = len(corpus["meeting_transcripts"])
    for item in labels["topic_list"] + labels["specific_query_list"]:
        for first, last in item["relevant_text_span"]:
            assert 0 <= int(first) <= int(last) < size, (name, first, last, size)
    assert all(item["query"] and item["answer"] for item in labels["general_query_list"] + labels["specific_query_list"])
    turns += size
    queries += len(labels["general_query_list"]) + len(labels["specific_query_list"])
    source_path = root / ".source" / f"{name}.json"
    if source_path.exists():
        source = json.loads(source_path.read_bytes())
        assert hashlib.sha256(source_path.read_bytes()).hexdigest() == expected
        assert source == corpus | labels
assert {p.stem for p in (root / "corpus").glob("*.json")} == set(manifest["raw_sha256"])
assert {p.stem for p in (root / "labels").glob("*.json")} == set(manifest["raw_sha256"])
print(f"QMSum AMI: 3 meetings, {turns} turns, {queries} queries; all spans and SHA-256 checks pass")
