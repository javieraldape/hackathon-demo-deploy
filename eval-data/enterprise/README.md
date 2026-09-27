# EnterpriseRAG-Bench bounded sample

This is **public, synthetic enterprise content**, not real private-company data. It is a retrieval/answer-evaluation fixture for Scoped Brain: email (`gmail`), Slack-like discussion (`slack`), and meeting transcripts (`fireflies`). It has **no fact-level ACL ground truth**. Source/channel metadata or mentions of roles in text must not be treated as access labels. Do not train on the benchmark questions/answers; upstream requests that benchmark data stay out of training corpora.

## Contents and selection

- `corpus/{gmail,slack,fireflies}/`: 100 byte-for-byte original UTF-8 `.txt` members from the v1.0.0 release ZIPs: 35 Gmail, 35 Slack, 30 Fireflies; 791,747 content bytes. The path retains the original source and `dsid_...` identity. `manifest.json` records each original archive, path, ID and extracted-byte SHA-256.
- `labels/questions.jsonl`: 4 unchanged source JSONL lines (`qst_0004`, `qst_0009`, `qst_0014`, `qst_0041`), with gold answers, answer facts, and complete `expected_doc_ids` in the corpus. **Never ingest this file or the manifest as retrieval content.**
- Selection is deterministic: include all four questions' evidence; fill each source quota with archive-member names in lexicographic order whose content contains the case-insensitive byte string `marketplace`. Two questions concern marketplace onboarding/security directly; the pricing and private-upgrade questions broaden evidence modalities. Other marketplace records are contextual distractors, not verified supporting evidence. The bounded sample is not representative of the 500K+ document full benchmark, and no permission/user identity labels are supplied.

## Provenance and terms (retrieved 2026-09-27)

Dataset: [Onyx EnterpriseRAG-Bench](https://github.com/onyx-dot-app/EnterpriseRAG-Bench), release [v1.0.0](https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/tag/v1.0.0), tag target commit `56ba6a62cb66bf0a68ff995b1c423680980bf70a`. The **dataset card itself**, not only the repository code license, declares [`license: mit`](https://huggingface.co/datasets/onyx-dot-app/EnterpriseRAG-Bench/blob/69916e31c68aa5963c00248fd7f0bc12d04fd235/README.md). The release and card explicitly distribute documents/questions; the repository [MIT license](https://github.com/onyx-dot-app/EnterpriseRAG-Bench/blob/56ba6a62cb66bf0a68ff995b1c423680980bf70a/LICENSE) is copyright © 2026 DanswerAI, Inc. MIT permits redistribution with the copyright and permission notice retained. Accordingly, this sample carries the copyright notice and license terms below; the upstream project and release are attributed, with no endorsement implied.

Raw release artifacts (`https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/download/v1.0.0/<filename>`):

| Filename | SHA-256 |
| --- | --- |
| `questions.jsonl` | `f9524b9157cd43aae36b99333a124738804306ea6d07f332d49faa6d3d147905` |
| `gmail_slice_0001.zip` | `8cfa1ab1a8e20fb7df4fec756073cb668433c6384541ebffc89ac4144ea79c1f` |
| `slack_slice_0001.zip` | `140dae8eeaab37c4e06c42020c4d4b11641aba6f7559583f9a83b8bb1c5a42c6` |
| `fireflies_slice_0001.zip` | `799e856058d1e92301bcbfc01fb903f16463092bfc9c42b3e9144db6fe742707` |

MIT License. Copyright (c) 2026 DanswerAI, Inc. Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: the above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Recreate and expand

Run `python3 eval-data/enterprise/fetch.py` from any directory, then `python3 eval-data/enterprise/validate.py`. Standard library only. The fetcher downloads and verifies pinned release asset hashes, extracts exact original bytes, and writes a generated mapping manifest. `.source/` is transient cache, not part of the delivered dataset; remove it after use. To expand, download a named release slice, independently record its SHA-256, then run `python3 eval-data/enterprise/fetch.py --expand slack --slice 2 --sha256 <64-hex-digest>` (or `gmail`/`fireflies`). This extracts the entire selected slice into `expanded/` without mixing it with the bounded corpus or benchmark labels. Additional asset hashes are caller-supplied; the four pinned sample assets above are verified automatically. This is collection only, not a fact-access evaluator.
