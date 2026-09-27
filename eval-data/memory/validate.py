import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def read_jsonl(name):
    return [json.loads(line) for line in (ROOT / name).read_text(encoding="utf-8").splitlines()]


corpus = read_jsonl("corpus.jsonl")
questions = read_jsonl("questions.jsonl")
labels = read_jsonl("labels.jsonl")
assert len(corpus) == len(questions) == len(labels) == manifest["selection"]["selected_record_count"]
ids = [row["record_id"] for row in corpus]
assert ids == [row["record_id"] for row in questions] == [row["record_id"] for row in labels]
assert all("answer" not in row and "question" not in row for row in corpus)
assert all("answer_session_ids" not in row and "has_answer" not in str(row) for row in corpus)
assert all(session["turns"] for row in corpus for session in row["sessions"])
for name, info in manifest["artifacts"].items():
    data = (ROOT / name).read_bytes()
    assert len(data) == info["bytes"]
    assert hashlib.sha256(data).hexdigest() == info["sha256"]
total = sum((ROOT / name).stat().st_size for name in manifest["artifacts"])
assert total <= 10 * 1024 * 1024, f"committed artifacts exceed 10 MiB: {total}"
print(f"OK: {len(corpus)} records, {total} bytes, {len({q['question_type'] for q in questions})} question types")
