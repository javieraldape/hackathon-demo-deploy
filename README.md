# Scoped Brain demo deployment

Deployment code and pinned patches for a Telegram → GBrain → QM workflow on Ubuntu 24.04. An allowlisted Telegram owner captures a meeting transcript; Haiku extracts facts, Jev classifies them, and deterministic code publishes them into separately authorized sources in the **existing GBrain**. QM exposes distinct authenticated `admin` and `intern` accounts through a loopback identity gateway on port **8188**.

The repository reproduces the software, not an existing user's brain. Credentials, authenticated sessions, the QM database, GBrain state, OpenClaw profile, private transcripts, and backup archives are deliberately excluded. Restoring existing memories requires an operator-supplied, consistent private backup and runtime configuration. Installing code does not provision accounts, scoped sources, OAuth clients, or a working bot.

## Security boundary

- The gateway verifies each account and forwards a short-lived signed QM identity. Set `PORTAL_LOCAL_AUTH_BYPASS=0`; never publish QM's raw portal or API ports.
- Only the mapped admin in a matching personal conversation can recall named-scope and vault information. Interns, rooms, unknown principals, and missing or mismatched scope context are limited to shared information. Prompt claims cannot grant access.
- QM's dedicated OAuth client can call only `qm_recall`. Telegram capture uses a separate client restricted to `capture_telegram_transcript`. Generic write tools must not provide a fallback into shared memory.
- Classification finishes before publication. Incomplete publication blocks remote reads until operator recovery. Live capture uses the existing server's resident engine, never a second opener of its PGLite datastore.

These are enforced code and runtime-configuration contracts, not a claim of exhaustive security certification. Host/database owners are outside the scoped-reader boundary.

## Start here

1. Read [installation and private restore](docs/INSTALL-RESTORE.md) before running scripts, especially on a host with existing state.
2. Complete the operator wiring in [the scoped workflow runbook](docs/SCOPED-WORKFLOW.md). The old single-user admin preview is not a substitute for the identity gateway.
3. Check the flow with [synthetic acceptance tests and public fixtures](docs/VALIDATION.md), using separate admin/intern sessions and inspecting raw tool output as well as answers.

For a configured bot, send `/capture_meeting arm` in its allowlisted direct message, approve the native binding if requested, send one pasted transcript or one UTF-8 `.txt` file (at most 20,000 bytes), and wait for a committed receipt. Send `/capture_meeting done` to return to ordinary chat. Inline command transcripts, PDFs, voice, images, and multi-file uploads are unsupported.

## Repository map

| Path | Purpose |
| --- | --- |
| `versions.env` | Exact QM/GBrain revisions and OpenClaw version |
| `patches/` | Scoped GBrain enforcement, trusted QM context, and OpenClaw 2026.9.6 native binding fixes |
| `integration/qm-identity-gate.ts` | Account authentication and signed QM session gateway |
| `scripts/`, `templates/` | Host installation/lifecycle helpers and non-secret configuration examples |
| `openclaw/`, `jev/` | Locked OpenClaw packages and hash-pinned official TypeSafe SDK |
| `eval-data/` | Public evaluation fixtures, provenance, licenses, and collection/validation scripts |

Upstream source is fetched at its pins, not vendored as a second application. See [source pins and attribution](docs/SOURCES.md). Public fixtures are not a production benchmark or proof of end-to-end authorization. No demo transcript is automatically restored or ingested.

Cloud machine sleep can stop services. This repository does not promise continuous availability; check service health before a demonstration and keep only one Telegram poller active.
