# LongMemEval cleaned sample

This directory contains a bounded sample of the official `xiaowu0162/longmemeval-cleaned` Hugging Face dataset, pinned to revision `98d7416c24c778c2fee6e6f3006e7a073259d48f`. The sample uses the cleaned **oracle** split: each selected source record contains only its answer-relevant history sessions. It is a long-term conversational memory/fact-retrieval benchmark sample, not a real-user data leak benchmark.

`corpus.jsonl` is the ingestible data only. `questions.jsonl` holds evaluation prompts and question metadata. `labels.jsonl` holds gold answers, answer-session IDs, and the per-turn `has_answer` annotation. Do not load the question or label files into the system under evaluation. The deterministic `fetch_sample.py` obtains the pinned upstream source, chooses the first four non-abstention records in each available question type and the first six abstentions, retains source ordering, separates the fields, and removes `has_answer` from corpus turns. Original source records are not redistributed; the manifest records their fetched SHA-256 and fully describes the transformations.

The source dataset card declares MIT. `source-card.md` preserves that card and `LICENSE.txt` preserves the MIT license text from the associated source repository at the pinned revision listed in `manifest.json`. These are the upstream dataset's published license statements; this sample has not been reviewed for any restrictions beyond them.

Run `python3 fetch_sample.py` to regenerate; it requires only the Python standard library and internet access. Run `python3 validate.py` for local structural, separation, hash, and size checks. Retrieval date, exact revisions, source checksum, artifact checksums, sizes, and sample counts are recorded in `manifest.json`.
