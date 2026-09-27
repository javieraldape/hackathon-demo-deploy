# Source pins and attribution

`versions.env`, `openclaw/package-lock.json`, and `jev/requirements.txt` are the executable pin records. Preserve them alongside custom patches; do not apply version-specific patches to moving upstream branches.

| Component | Pin | Attribution / terms |
| --- | --- | --- |
| [QM](https://github.com/yc-software/qm) | `5a5cb51260b13000dda5d890d40c877c88d87555` | MIT; copyright 2026 QM contributors |
| [GBrain](https://github.com/garrytan/gbrain) | `v0.59.0.0`, commit `e78f1c38b947b053f3a46881340f74f316be855a` | MIT; copyright 2026 Garry Tan |
| [OpenClaw](https://www.npmjs.com/package/openclaw) | `2026.9.6`, exact artifacts in lockfile | MIT in package metadata; retain the installed upstream notice |
| [`@openclaw/codex`](https://www.npmjs.com/package/@openclaw/codex) | `2026.9.6`, exact artifact in lockfile | Separate package; retain its distributed terms, not an inferred license from OpenClaw |
| Official TypeSafe SDK | `typesafe-sdk==0.7.2`, dependency hashes in `jev/requirements.txt` | TypeSafe's SDK for hosted Jev; preserve its distributed notices and applicable service terms |

Upstream application source is fetched rather than vendored wholesale. The patch bundle contains this integration's code and tests plus the context needed to apply them, not third-party repository history. Upstream license and copyright obligations still apply. Preserve upstream license files in installed/redistributed source and packages and applicable third-party notices. This document is attribution, not a replacement license for every dependency or a blanket license grant for private runtime data.

The official SDK is not the similarly named third-party `jev-cli`. Hosted Jev and Anthropic access remain external service dependencies. The scoped extraction code specifies `claude-haiku-4-5-20251001`; Jev uses the hosted `jev-latest` selector, which can change independently of repository pins. Locked software therefore does not guarantee bit-for-bit model outputs or permanent provider availability.

## Public dataset provenance

Keep each dataset's manifests, licenses, source cards, and transformation descriptions with any redistributed fixture:

- [EnterpriseRAG-Bench](../eval-data/enterprise/README.md): Onyx/DanswerAI, release `v1.0.0`, source commit `56ba6a62cb66bf0a68ff995b1c423680980bf70a`; published MIT dataset terms and retained notice. Respect the upstream request to exclude benchmark data from training.
- [QMSum/AMI](../eval-data/meetings/README.md): QMSum revision `83d7768c1f2b4dfeb091385d3dc7e239b8e5bb7e`, MIT, copyright 2021 Yale-LILY; underlying AMI Meeting Corpus is **CC BY 4.0**, credited to the University of Edinburgh/AMI Consortium. Preserve both notices and the description of transcript/annotation splitting. Other meeting domains can have different terms.
- [LongMemEval](../eval-data/memory/README.md): `xiaowu0162/longmemeval-cleaned`, revision `98d7416c24c778c2fee6e6f3006e7a073259d48f`; upstream card declares MIT. The fixture preserves its source card and license and records oracle-split transformations.
- [OrgAccess](../eval-data/permissions/README.md): `respai-lab/orgaccess`, revision `c1564174c8f29ff32c78c6f6e27a5fe3ac2ac949`; upstream card declares MIT. The fixture preserves its source card, license, and deterministic sampling details.

These are bounded public fixtures, not private demo transcripts or production benchmark results. Dataset-specific documents are the detailed provenance record; no upstream affiliation or endorsement is implied.
