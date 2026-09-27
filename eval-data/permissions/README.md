# OrgAccess representative permission cases

This directory contains a small, deterministic sample from the `respai-lab/orgaccess` Hugging Face dataset, pinned to dataset revision `c1564174c8f29ff32c78c6f6e27a5fe3ac2ac949`. The sample takes three examples of each expected decision (`full`, `partial`, `rejected`) from each difficulty split (`easy`, `medium`, `hard`), in original row order. `fetch_sample.py` scans small pages from the Hub rows API and stops after collecting that quota for each split and outcome.

`corpus.jsonl` contains only roles and permission contexts. `questions.jsonl` contains the employee requests. `labels.jsonl` contains expected decisions and rationales. Keep question and label files out of the system being evaluated. `manifest.json` records the exact source revisions, row indices, per-row hashes, retrieval timestamp, scan extents, transformations, and artifact checksums. The source fields are preserved except that the source's JSON-encoded permissions string is parsed into a JSON object.

The upstream Hugging Face card declares MIT; `source-card.md` preserves the upstream repository README and `LICENSE.txt` the MIT license text at the pinned repository revision. The dataset card describes OrgAccess as synthetic; its cases evaluate organizational permission decisions, not fact-level privacy leakage or end-to-end disclosure from memory.

Run `python3 fetch_sample.py` to regenerate; only the Python standard library is needed. Run `python3 validate.py` for local structure, separation, checksums, and total-size checks.
