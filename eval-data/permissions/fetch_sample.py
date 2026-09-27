#!/usr/bin/env python3
"""Fetch a small, pinned, stratified OrgAccess sample via the HF rows API."""

import hashlib
import json
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


REVISION = "c1564174c8f29ff32c78c6f6e27a5fe3ac2ac949"
REPOSITORY_REVISION = "c65ef95f7a8821098906012c4236a4fcd8144f9b"
DATASET = "respai-lab/orgaccess"
SPLITS = ("easy", "medium", "hard")
TARGET_PER_DECISION = 3
PAGE_SIZE = 100
MAX_ROWS_PER_SPLIT = 10_000
API_BASE = "https://datasets-server.huggingface.co/rows"
REPO = Path(__file__).resolve().parent


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "ScopedBrain-eval-data/1.0"})
    for attempt in range(7):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return response.read(), response.headers
        except HTTPError as error:
            if error.code != 429 or attempt == 6:
                raise
            time.sleep(min(60, int(error.headers.get("Retry-After", 2 ** attempt))))


def rows_url(split, offset, length):
    params = urllib.parse.urlencode({
        "dataset": DATASET,
        "config": "default",
        "split": split,
        "offset": offset,
        "length": length,
        "revision": REVISION,
    })
    return f"{API_BASE}?{params}"


def write_jsonl(path, records):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    selected = []
    queries = []
    labels = []
    scanned = {}
    row_source_hashes = {}
    for split in SPLITS:
        found = Counter()
        offset = 0
        total_rows = None
        while offset < MAX_ROWS_PER_SPLIT and any(found[label] < TARGET_PER_DECISION for label in ("full", "partial", "rejected")):
            body, headers = fetch(rows_url(split, offset, PAGE_SIZE))
            assert headers.get("x-revision") == REVISION, f"Hub returned unexpected revision: {headers.get('x-revision')}"
            page = json.loads(body)
            total_rows = page["num_rows_total"]
            for item in page["rows"]:
                row = item["row"]
                decision = row["expected_response"]
                if decision not in ("full", "partial", "rejected") or found[decision] >= TARGET_PER_DECISION:
                    continue
                index = item["row_idx"]
                record_id = f"{split}:{index}"
                permission_text = row["permissions"]
                permissions = json.loads(permission_text)
                selected.append({"record_id": record_id, "split": split, "source_row": index,
                                 "user_role": row["user_role"], "permissions": permissions})
                queries.append({"record_id": record_id, "query": row["query"]})
                labels.append({"record_id": record_id, "expected_response": decision, "rationale": row["rationale"]})
                row_source_hashes[record_id] = hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                found[decision] += 1
            offset += PAGE_SIZE
            if offset >= total_rows:
                break
        scanned[split] = {"rows_scanned": min(offset, total_rows or offset), "source_rows": total_rows,
                          "selected_by_decision": dict(found)}
        if any(found[label] < TARGET_PER_DECISION for label in ("full", "partial", "rejected")):
            raise RuntimeError(f"Could not find {TARGET_PER_DECISION} of every decision in {split}: {found}")

    corpus_path = REPO / "corpus.jsonl"
    questions_path = REPO / "questions.jsonl"
    labels_path = REPO / "labels.jsonl"
    write_jsonl(corpus_path, selected)
    write_jsonl(questions_path, queries)
    write_jsonl(labels_path, labels)
    readme_url = f"https://raw.githubusercontent.com/respailab/orgaccess/{REPOSITORY_REVISION}/README.md"
    license_url = f"https://raw.githubusercontent.com/respailab/orgaccess/{REPOSITORY_REVISION}/LICENSE"
    (REPO / "source-card.md").write_bytes(fetch(readme_url)[0])
    (REPO / "LICENSE.txt").write_bytes(fetch(license_url)[0])
    artifacts = {}
    for path in (corpus_path, questions_path, labels_path, REPO / "source-card.md", REPO / "LICENSE.txt"):
        artifacts[path.name] = {"sha256": digest(path), "bytes": path.stat().st_size}
    manifest = {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "dataset": DATASET,
            "dataset_revision": REVISION,
            "repository_revision_for_license_and_card": REPOSITORY_REVISION,
            "rows_api": API_BASE,
            "license": "MIT (Hugging Face dataset card metadata)",
        },
        "selection": {
            "rule": f"Within each source split, select the first {TARGET_PER_DECISION} rows of each expected_response class (full, partial, rejected), scanning source row order in pages of {PAGE_SIZE}.",
            "scanned": scanned,
            "selected_count": len(selected),
            "selected_by_split": {split: sum(row["split"] == split for row in selected) for split in SPLITS},
            "selected_by_decision": dict(Counter(row["expected_response"] for row in labels)),
            "source_row_content_sha256": row_source_hashes,
        },
        "transformations": [
            "Separate user role and parsed permissions context (corpus.jsonl), natural-language request (questions.jsonl), and expected decision plus rationale (labels.jsonl).",
            "Parse the source permissions JSON string into a JSON object; preserve role, query, expected decision, and rationale content otherwise unchanged.",
            "Synthetic role-permission cases only; not a real-world sensitive-data leak or fact-level privacy benchmark.",
        ],
        "artifacts": artifacts,
    }
    (REPO / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Selected {len(selected)} rows; corpus={corpus_path.stat().st_size} bytes; scanned={scanned}")


if __name__ == "__main__":
    main()
