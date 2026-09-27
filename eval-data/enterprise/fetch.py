#!/usr/bin/env python3
"""Recreate the bounded EnterpriseRAG-Bench sample from pinned release assets."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parent
BASE = "https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/download/v1.0.0/"
SOURCES = {
    "gmail": "8cfa1ab1a8e20fb7df4fec756073cb668433c6384541ebffc89ac4144ea79c1f",
    "slack": "140dae8eeaab37c4e06c42020c4d4b11641aba6f7559583f9a83b8bb1c5a42c6",
    "fireflies": "799e856058d1e92301bcbfc01fb903f16463092bfc9c42b3e9144db6fe742707",
}
QUESTIONS_SHA = "f9524b9157cd43aae36b99333a124738804306ea6d07f332d49faa6d3d147905"
QUESTION_IDS = ("qst_0004", "qst_0009", "qst_0014", "qst_0041")
LIMITS = {"gmail": 35, "slack": 35, "fireflies": 30}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def download(name, expected):
    path = ROOT / ".source" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(BASE + name, timeout=120) as response:
            path.write_bytes(response.read())
    if digest(path.read_bytes()) != expected:
        raise ValueError(f"Source checksum mismatch: {name}")
    return path


def sample():
    questions_path = download("questions.jsonl", QUESTIONS_SHA)
    lines = questions_path.read_bytes().splitlines(keepends=True)
    questions = {json.loads(line)["question_id"]: line for line in lines}
    chosen = [questions[qid] for qid in QUESTION_IDS]
    evidence = {doc_id for line in chosen for doc_id in json.loads(line)["expected_doc_ids"]}
    records = []
    for source, expected in SOURCES.items():
        with zipfile.ZipFile(download(f"{source}_slice_0001.zip", expected)) as archive:
            names = archive.namelist()
            by_id = {re.search(r"dsid_[0-9a-f]+", name).group(): name for name in names}
            selected = {by_id[doc_id] for doc_id in evidence if doc_id in by_id}
            candidates = sorted(name for name in names if b"marketplace" in archive.read(name).lower())
            selected.update(name for name in candidates if len(selected) < LIMITS[source])
            if len(selected) != LIMITS[source]:
                raise ValueError(f"Too few candidate documents: {source}")
            for name in sorted(selected):
                if len(Path(name).parts) != 2 or Path(name).parts[0] != source or not name.endswith(".txt"):
                    raise ValueError(f"Unexpected archive path: {name}")
                data = archive.read(name)
                target = ROOT / "corpus" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                records.append({"path": str(target.relative_to(ROOT)), "doc_id": re.search(r"dsid_[0-9a-f]+", name).group(), "archive": f"{source}_slice_0001.zip", "sha256": digest(data)})
    (ROOT / "labels").mkdir(exist_ok=True)
    labels = b"".join(chosen)
    (ROOT / "labels" / "questions.jsonl").write_bytes(labels)
    (ROOT / "manifest.json").write_text(json.dumps({"release": "v1.0.0", "labels_sha256": digest(labels), "documents": records}, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expand", choices=SOURCES, help="Download an additional complete source slice instead of recreating the sample")
    parser.add_argument("--slice", type=int, help="Additional slice number (starts at 1)")
    parser.add_argument("--sha256", help="Expected SHA-256 of the additional release asset")
    args = parser.parse_args()
    if args.expand:
        if not args.slice or not args.sha256 or not re.fullmatch(r"[0-9a-f]{64}", args.sha256):
            parser.error("--expand requires --slice NUMBER and --sha256 HEX")
        name = f"{args.expand}_slice_{args.slice:04d}.zip"
        archive_path = download(name, args.sha256)
        with zipfile.ZipFile(archive_path) as archive:
            for name in archive.namelist():
                if len(Path(name).parts) != 2 or Path(name).parts[0] != args.expand or not name.endswith(".txt"):
                    raise ValueError(f"Unexpected archive path: {name}")
                target = ROOT / "expanded" / f"{args.expand}_slice_{args.slice:04d}" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(name))
        print(f"Expanded {len(archive.namelist())} documents from {archive_path.name}")
    else:
        if args.slice or args.sha256:
            parser.error("--slice and --sha256 require --expand")
        sample()


if __name__ == "__main__":
    main()
