# Validation and public fixtures

## What can be checked from Git

Run the repository's local tests and package/patch checks before deployment:

```sh
python3 -m unittest discover -s tests -v
bun test tests/scoped-preview.test.ts
QM_SOURCE=/absolute/path/to/patched/qm bun test integration/qm-identity-gate.test.ts
```

The gateway compatibility test imports the pinned QM session verifier from the explicitly supplied checkout; it does not need production credentials. The installer validates pinned revisions and applies patch series before building. Patch application tests use disposable fixtures, not a running brain.

For the public datasets, run from the repository root:

```sh
for dataset in enterprise meetings memory permissions; do
  python3 "eval-data/$dataset/validate.py" || exit 1
done
```

These validate fixture structure, separation, hashes, and size, not live authorization. If required artifacts are absent, follow that dataset's documented fetch step; do not interpret a missing corpus as a pass. Keep labels, questions, answers, manifests, and provenance outside the searchable brain. Never ingest `eval-data/` recursively.

The [dataset overview](../eval-data/README.md), [permission contract](../eval-data/PERMISSION-CONTRACT.md), [evaluation brief](../eval-data/EVALUATION-BRIEF.md), and [execution handoff](../eval-data/CLOUD-HANDOFF.md) preserve preparation work. Treat planned evaluator work there as a plan, not evidence that an independent leak harness or production benchmark exists.

| Fixture | Useful coverage | Limit |
| --- | --- | --- |
| [EnterpriseRAG-Bench](../eval-data/enterprise/README.md) | Bounded synthetic enterprise retrieval and answers | No fact-level access-control oracle; not the full benchmark |
| [QMSum/AMI](../eval-data/meetings/README.md) | Multi-speaker meeting retrieval and supporting spans | Speaker roles are not authorization labels |
| [LongMemEval](../eval-data/memory/README.md) | Oracle evidence reading, updates, temporal reasoning, abstention | Relevant-session inputs do not test full-history retrieval; isolate unrelated cases |
| [OrgAccess](../eval-data/permissions/README.md) | Synthetic permission decision reasoning | Correct reasoning does not prove API enforcement or memory non-disclosure |

Upstream models may have seen public benchmark answers. Use separately authored fictional values for disclosure tests, with allowed readers and expected answers defined **before** classification. Preserve failed results as well as successes privately. These fixtures and bounded synthetic tests are not a production benchmark, exhaustive attack coverage, or a general privacy proof.

Checked-in synthetic test definitions do not imply corresponding data exists in a live brain. Create a new explicitly approved synthetic case if a fresh end-to-end check is needed; do not restore deleted fixture state implicitly.

## Acceptance on a configured deployment

Unit tests of hooks or local agent invocations do not prove Telegram transport. A live acceptance run requires an actual Telegram message and independently authenticated QM sessions. Use synthetic content and keep receipts, raw output, screenshots, logs, and identities outside the repository.

1. Check service health and existing shared-memory retrieval before the test. Confirm only one Telegram poller and one owner of the PGLite datastore, local auth bypass disabled, and only the identity gateway exposed.
2. Exercise real owner arm/approval, pasted text capture, a staged `.txt` capture, and done/ordinary chat. Confirm committed receipts and source placement, not merely successful transport or a model response.
3. In fresh independent admin and intern QM sessions, ask the same unseeded questions. The authorized admin personal session should retrieve the test's shared and private markers. Intern answers **and raw tool output** must contain the expected shared markers and no named-scope/vault markers.
4. Check that prompt claims of admin status, forged personal scopes, cross-user session access, restricted direct lookup, rooms, and missing/unknown identity context cannot increase access. Exercise generic read calls with the QM credential and raw write calls through Telegram's ordinary agent path; denials must be enforced, not merely omitted from a tool listing.
5. Test malformed/time-out classification, unsupported uploads, duplicates, and partial-publication failure in a disposable isolated test environment. Failures must not fall back to shared writes, and a retained publication marker must block remote reads. Do not inject destructive failures into a live private brain.
6. Recheck existing memories, shared retrieval, ordinary chat, and service health. Record exactly which behaviors were checked and which remain untested; installation success is not end-to-end acceptance.

Hosted Haiku/Jev checks require credentials and may incur usage charges. Never include keys or private transcript content in test output, commands committed to Git, or published reports.
