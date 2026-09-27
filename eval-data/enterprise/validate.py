#!/usr/bin/env python3
"""Validate local corpus integrity and complete evidence references."""

import collections
import hashlib
import json
from pathlib import Path


root = Path(__file__).resolve().parent
manifest = json.loads((root / "manifest.json").read_text())
records = manifest["documents"]
assert len(records) == 100
assert len({record["doc_id"] for record in records}) == 100
assert len({record["path"] for record in records}) == 100
assert collections.Counter(record["archive"].split("_")[0] for record in records) == {"gmail": 35, "slack": 35, "fireflies": 30}
for record in records:
    path = root / record["path"]
    assert path.is_file() and path.resolve().is_relative_to(root.resolve())
    assert path.name.startswith(record["doc_id"] + "__")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
assert {str(path.relative_to(root)) for path in (root / "corpus").rglob("*.txt")} == {record["path"] for record in records}
labels_path = root / "labels" / "questions.jsonl"
assert hashlib.sha256(labels_path.read_bytes()).hexdigest() == manifest["labels_sha256"]
lines = labels_path.read_text().splitlines()
questions = [json.loads(line) for line in lines]
assert [question["question_id"] for question in questions] == ["qst_0004", "qst_0009", "qst_0014", "qst_0041"]
ids = {record["doc_id"] for record in records}
for question in questions:
    assert question["expected_doc_ids"] and set(question["expected_doc_ids"]) <= ids
    assert question["gold_answer"] and question["answer_facts"]
print(f"Enterprise: {len(records)} documents, {len(questions)} questions, {sum((root / r['path']).stat().st_size for r in records)} corpus bytes; all references and SHA-256 checks pass")
