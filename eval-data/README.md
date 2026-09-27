# Scoped Brain evaluation data

This directory contains public benchmark material and reproducible collection instructions, not the private demo backup. Dataset-specific READMEs document sources, licenses, sampling, and limitations. Do not ingest this directory recursively: evaluation questions, answers, access expectations, and provenance must stay outside the searchable brain.

## What each collection tests

- `enterprise/`: realistic company documents and retrieval questions. It is not a fact-level authorization oracle.
- `meetings/`: long, multi-speaker discussions and supporting answer spans, subject to the source corpus's redistribution terms.
- `memory/`: LongMemEval evidence and questions for recall, updates, temporal reasoning, and abstention. An adapted subset is not an official full-benchmark score.
- `permissions/`: role and permission reasoning examples. Correct access decisions here do not establish that GBrain's APIs enforce them.

## Security evaluation still to author

The checked-in starter set contains 100 enterprise documents with four retrieval questions, three AMI meetings with 27 query-answer pairs, 30 LongMemEval oracle cases, and 27 OrgAccess permission cases. LongMemEval oracle inputs contain evidence sessions rather than a full distractor haystack: they test evidence reading but do not establish long-history retrieval performance. Keep each LongMemEval case in its own evaluation namespace instead of combining unrelated users' histories.

Run all local integrity checks from the repository root:

```bash
for dataset in enterprise meetings memory permissions; do
  python3 "eval-data/$dataset/validate.py" || exit 1
done
```

Fetch scripts and dataset READMEs describe reproducible downloads. Source caches, expanded corpora, and Python bytecode remain ignored by Git. The starter set deliberately avoids downloading the entire enterprise benchmark into the repository.

An independent fixture author must define fact-level allowed readers, prohibited readers, supporting spans, and expected answers before running the classifier. Never use the classifier's own output as ground truth. Public benchmark answers can be memorized by models; use separately authored fictional names and values for controlled disclosure tests, and identify those cases as synthetic adaptations.

Ask each sensitive question as both an authorized and an unauthorized identity. Test raw API responses as well as generated answers, including citations, metadata, deleted versions, repeated ingestion, new scopes, and obsolete manager copies. A refusal after restricted evidence reached the answering model still counts as an enforcement failure.

Compare open access, whole-page hiding, and fact-scoped access on identical inputs. Report unauthorized disclosures separately from authorized answer accuracy, and preserve a held-out set. Exact string checks alone miss paraphrased disclosures: combine normalization, semantic assessment, and human review. Zero observed leaks is a bounded test result, not proof that all possible queries are safe.

## Safety

These files do not configure permissions or modify the running demo. Do not put API keys, generated credentials, PostgreSQL dumps, GBrain/OpenClaw state, or private restore material here. Downloaded full corpora and scratch files should remain outside Git unless explicitly reviewed for redistribution and size.
