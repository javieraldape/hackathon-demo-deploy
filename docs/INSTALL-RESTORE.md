# Installation and private restore

## Choose the operation first

**Fresh code installation** fetches pinned dependencies and applies the repository's customizations. It cannot recover private memory or create an authenticated scoped deployment by itself. **Private restore** additionally requires the existing database, brain state, profile, and credentials. **An existing live host** must not be treated as a fresh target: inspect its state, take a consistent private backup, and plan the change before invoking install, restore, adoption, or lockdown helpers.

Use Ubuntu 24.04 with Node 24.18.0 or later, npm, Bun 1.3.14, Git, Docker with socket access, OpenSSL, `ss`, `tmux`, and `uv`. Docker socket access is privileged. The installer uses Python 3.13 for the official hash-pinned `typesafe-sdk`, and builds QM's local sandbox image. Network access to pinned upstreams and package registries is required.

Set `DEMO_RUNTIME_ROOT` to an absolute private directory outside this checkout if overriding the script default. Keep runtime state, generated environment files, downloads containing private data, and backups out of Git and Docker build contexts. Run from the repository root on an approved **fresh** target:

```sh
scripts/install
scripts/status
```

Review the scripts' output before continuing. Installation is not evidence that OAuth, model access, Telegram transport, scoped policy, or restored identity mapping works. Do not run upstream postinstall or migration commands against a live brain casually; the packaged GBrain dependency install deliberately disables lifecycle scripts. Native OpenClaw bundle patches target **2026.9.6 only**, in numeric order; a patch mismatch requires review, not a forced application.

## Private material needed to restore an existing brain

Obtain a consistent snapshot through an authenticated private transfer, not a chat attachment, public preview, or Git. Stop/quiesce the relevant writers when making a filesystem snapshot; copying an actively written PGLite directory is not a consistency guarantee. Preserve the entire existing brain, including its database, scoped manifests/receipts, authorization state, and publication markers. Do not create a second brain to stand in for a missing backup.

The legacy restore helper expects this relative layout:

```text
<private-backup>/
  qm.pgcustom
  gbrain-home/.gbrain/              # complete consistent tree, including config.json
  openclaw/                        # complete profile, including openclaw.json
  hackathon/                       # private workspace and memory
  credentials/hackathon/           # private OAuth/token material
  credentials/codex/auth.json
```

This layout alone is not a complete scoped-deployment inventory. Preserve current gateway configuration, QM runtime/provider configuration, capture-client credentials, and process-environment configuration separately when they live outside those directories. Older backups may predate the gateway and scoped grants; an operator must reconcile them rather than assuming a restore enables the current workflow.

Use directory mode `0700` and secret-file mode `0600`. Permission bits are not encryption: encrypt backups stored externally. The restore helper refuses existing target state, an existing database container, symlinks, and group/world-readable backup entries. Investigate a refusal; do not remove protections or delete state merely to get past it.

On a fresh target, the installer generates a matching private PostgreSQL/QM environment pair. The restore helper preserves that new database password rather than importing credentials for a different container. Do not copy physical PostgreSQL files from another operating system or mix a database with another container's password. Use the logical custom-format QM dump.

After inspection, invoke the helper with the actual private source-path metadata supplied by the operator:

```sh
scripts/restore "$PRIVATE_BACKUP" "$SOURCE_MAC_HOME" "$SOURCE_CLOUD_RUNTIME"
```

The second argument identifies the original macOS home for the legacy path rewrite; the optional third identifies the prior cloud runtime. These are private runtime inputs, not values to check into this repository. A backup from a different layout requires a reviewed migration, not invented path values. The helper starts the target database to load the dump; it does not authorize Telegram cutover or verify the scoped workflow.

## Operator configuration remains required

Before exposing anything, verify the exact source pins and applied patches, restored identities and grants, private file permissions, rewritten runtime paths, and the configuration in [SCOPED-WORKFLOW.md](SCOPED-WORKFLOW.md). Keep API keys in a secure process environment or private credential store. Haiku/Jev and other hosted providers require valid credentials, may incur usage charges, and receive the inputs described in the workflow runbook.

Never expose raw QM ports or the GBrain admin surface. The account gateway must use the exact public HTTPS origin, bind locally on port 8188, and share the correct signing secret with QM. Local auth bypass must remain disabled. A stale single-user preview or old generic MCP registration must not remain an alternate path around scoped authorization.

Start services only after reviewing the configuration and confirming the old Telegram poller is stopped. Use `scripts/status` to check process state, then the acceptance checks in [VALIDATION.md](VALIDATION.md) to check behavior. Keep private diagnostics private. Idle cloud sleep is not an always-on hosting arrangement; inspect state and restore services deliberately after waking.
