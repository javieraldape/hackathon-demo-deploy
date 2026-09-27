#!/usr/bin/env python3
"""Recreate the AMI portion of the QMSum sample at a pinned revision."""

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
REVISION = "83d7768c1f2b4dfeb091385d3dc7e239b8e5bb7e"
URL = f"https://raw.githubusercontent.com/Yale-LILY/QMSum/{REVISION}/data/Product/test/"
SOURCES = {
    "ES2004a": "911e56db0d8482f1e730bae0a8fcf0ab0095c94abb000ba0516e975fa6e48b31",
    "ES2004b": "5ed3c79e6784827652a2cdfaf2922c377aa386d8501b4a2039e51fb00a4d294d",
    "ES2004c": "31815196407111dba01f8b8cbfa31cd07fb8a682e4005bae7846893ab93a6778",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def download(name, expected):
    path = ROOT / ".source" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(URL + name + ".json", timeout=60) as response:
            path.write_bytes(response.read())
    if sha(path.read_bytes()) != expected:
        raise ValueError(f"Source checksum mismatch: {name}")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expand", help="Additional AMI Product/test meeting ID, e.g. ES2004d")
    parser.add_argument("--sha256", help="Expected SHA-256 of the additional raw JSON")
    args = parser.parse_args()
    if args.expand:
        if not args.sha256 or len(args.sha256) != 64 or not all(c in "0123456789abcdef" for c in args.sha256) or not args.expand.isalnum():
            parser.error("--expand ID requires --sha256 HEX")
        names = {args.expand: args.sha256}
    else:
        if args.sha256:
            parser.error("--sha256 requires --expand")
        names = SOURCES
    for name, expected in names.items():
        raw = download(name, expected)
        source = json.loads(raw.read_bytes())
        corpus = {"meeting_transcripts": source["meeting_transcripts"]}
        labels = {key: value for key, value in source.items() if key != "meeting_transcripts"}
        corpus_path = ROOT / ("expanded/corpus" if args.expand else "corpus") / f"{name}.json"
        labels_path = ROOT / ("expanded/labels" if args.expand else "labels") / f"{name}.json"
        corpus_path.parent.mkdir(parents=True, exist_ok=True)
        labels_path.parent.mkdir(parents=True, exist_ok=True)
        corpus_path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n")
        labels_path.write_text(json.dumps(labels, ensure_ascii=False, indent=2) + "\n")
    if not args.expand:
        (ROOT / "manifest.json").write_text(json.dumps({"revision": REVISION, "raw_sha256": SOURCES, "corpus_sha256": {name: sha((ROOT / "corpus" / f"{name}.json").read_bytes()) for name in SOURCES}, "labels_sha256": {name: sha((ROOT / "labels" / f"{name}.json").read_bytes()) for name in SOURCES}}, indent=2) + "\n")


if __name__ == "__main__":
    main()
