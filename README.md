# Hackathon demo host deployment (Ubuntu 24.04)

This Git repository is **only deployment code**. The private QM database, GBrain memory, OpenClaw profile, JEV API key, OAuth material, Telegram token, Codex login, logs, and dumps belong in the private runtime or secure environment, never here. A future Capy cloud machine cannot reproduce the live demo from Git alone: Javier must provide the private snapshot from his linked Mac or another backup. The current Mac directory is 0700 with 0600 secret files, **not encrypted at rest**; encrypt external backups. Do not ask an agent to read or print that material.

Pinned versions: `yc-software/qm` commit `5a5cb51260b13000dda5d890d40c877c88d87555` (the active Mac `hackathon/qm-local`, **not** `Projects/qm`), `garrytan/gbrain` tag `v0.59.0.0` at the commit in `versions.env`, and npm `openclaw@2026.9.6` plus `@openclaw/codex@2026.9.6` with their lockfile. Sources are cloned on the host; neither upstream repository is vendored.

## Layout and installation

The default private runtime is `~/.capy/work/hackathon-runtime/stage` (`DEMO_RUNTIME_ROOT` can override it with another absolute directory outside Git). The QM checkout is `stage/qm`, GBrain source is `stage/../tools/gbrain`, OpenClaw profile is `stage/openclaw`, GBrain state is `stage/gbrain-home/.gbrain`, and private env/auth is `stage/credentials`. Do not run the install or restore scripts on the already-live migration unless deliberately replacing it; this repository was validated without invoking them against that runtime.

Requires Ubuntu 24.04, Node 24.18.0+, npm, Bun 1.3.14, Git, Docker with socket access, OpenSSL, `ss`, `tmux`, and `uv`. `scripts/install` checks the pinned Git SHAs, runs QM's `npm ci` and web build, clones GBrain locally and runs `bun install --frozen-lockfile --ignore-scripts` so its global GitHub package failure (`patches/postgres@3.4.9.patch`) and host-brain postinstall migrations are avoided, and installs the locked OpenClaw packages under the ignored private runtime. It also installs TypeSafe's official JEV client into a Python 3.13 environment using `jev/requirements.txt` with hashes. On a fresh machine it generates a random PostgreSQL password in mode-0600 `credentials/postgres.env` and matching `credentials/qm.env`, configured for the later restored Codex login; **restore preserves this password pair**. If Postgres already exists without a matching private env pair, use `scripts/adopt-live` below. Do not commit generated credentials.

```bash
cd /workspace/hackathon-demo-deploy
scripts/install
scripts/status
```

Install also builds QM's pinned local sandbox image from the host checkout before enabling turns; this Docker build can take several minutes. Docker socket access is privileged. `scripts/start qm` does not silently substitute mock or memory persistence when a real credential or sandbox image is missing.

## Private snapshot contract and restore

Javier's actual private Mac snapshot is `~/.capy/work/hackathon-cloud-private-backup/`. On a later cloud machine retrieve it from the linked Mac through an authenticated private channel (not Git, chat, Capy preview, or a Docker build context); encrypt any external backup. The required layout is:

```
hackathon-cloud-private-backup/
  qm.pgcustom
  gbrain-home/.gbrain/config.json        # plus the entire consistent .gbrain tree/PGLite data
  openclaw/openclaw.json                 # plus the entire OpenClaw profile
  hackathon/                             # private workspace and memory
  credentials/hackathon/*                # private token/OAuth/owner material
  credentials/codex/auth.json            # private Codex login
```

There is deliberately **no `postgres.env` or `qm.env` in this Mac backup**. `scripts/install` creates a fresh matching pair for the new cloud Postgres container; `scripts/restore` leaves its password untouched, sets `HARNESS=codex` and `CODEX_AUTH_FILE=stage/credentials/codex/auth.json`, and restores the private source data. Do not copy Mac physical PostgreSQL files or mix credentials from different containers. The dump includes the existing QM MCP registration/admin grant.

On a **fresh** target with no database container and no existing GBrain/OpenClaw state, after `scripts/install`:

```bash
chmod 700 /absolute/private/hackathon-cloud-private-backup
find /absolute/private/hackathon-cloud-private-backup -type d -exec chmod 700 {} +
find /absolute/private/hackathon-cloud-private-backup -type f -exec chmod go-rwx {} +
chmod 600 /absolute/private/hackathon-cloud-private-backup/{qm.pgcustom,openclaw/openclaw.json,gbrain-home/.gbrain/config.json,credentials/codex/auth.json}
scripts/restore /absolute/private/hackathon-cloud-private-backup '/Users/your-mac-login'
```

`restore` checks all required backup paths/modes, custom-dump signature, symlinks, pinned QM source, generated env pair, empty target state, and absent target DB **before copying anything**. It copies `openclaw/`, `gbrain-home/.gbrain/`, `hackathon/`, and the private Codex/hackathon credentials, then rewrites known Mac workspace/token/profile paths and the old cloud stage root in GBrain/OpenClaw configs. Pass an optional third argument for an old cloud stage root other than `/home/user/.capy/work/hackathon-runtime/stage`. It starts loopback-only PostgreSQL 16, waits for its final TCP listener (not the temporary init socket), and pipes the private dump through `pg_restore` without displaying data. Failures go to a mode-0600 private diagnostics file. It refuses to overwrite populated target state. The private Mac backup intentionally omits two obsolete absolute links from `openclaw/plugin-skills`; restore calls `scripts/prepare-openclaw`, which registers pinned `@openclaw/codex` with `plugins install --force`, runs `doctor --fix` to recreate links, validates the config, and writes a private readiness marker. Plugin/doctor output stays in `stage/logs/openclaw-prepare.log`; inspect privately on failure. Review any remaining path references and the restored OAuth issuer privately; QM and GBrain both run on the **host**, so the existing QM MCP URL `127.0.0.1:3131` reaches the single GBrain HTTP service without private DB edits.

This snapshot captures state only as of its creation. Refresh the PostgreSQL dump and cold GBrain/OpenClaw files after later demo writes before relying on a new VM for current data; stop GBrain before copying its PGLite tree. Never copy an active PGLite directory or start two Telegram pollers against the same bot.

On the **already-running** cloud demo, `qm-dev-postgres` may exist while `credentials/postgres.env` and `qm.env` do not. After ensuring the pinned QM checkout, run `scripts/adopt-live [database-name]` **once** rather than `scripts/install` or `scripts/restore` against that live DB. It reads the current container credential in memory without printing it, writes the pair as 0600 private files, selects the single `qm_dev_*`/`qm` database (or requires an explicit name if ambiguous), sets `HARNESS=codex`/`CODEX_AUTH_FILE`, and verifies a PostgreSQL client connection. It never rotates a password or changes DB contents. On that live profile, run `scripts/prepare-openclaw` privately once if the readiness marker is absent. Do not use adoption on a fresh machine; install and restore are the fresh-machine path.

## Start, stop, and safe cutover

Use `scripts/start db`, then `scripts/start gbrain` (one host HTTP service at `127.0.0.1:3131`, with DCR enabled), then `scripts/start qm` (host dev-instance core `8081`, portal `8129`). QM's localhost admin bypass is **unsafe if published**. The browser in the machine's **Desktop tab** must open `http://localhost:8129` exactly; `127.0.0.1` fails QM's origin check. Never publish the portal, core, or GBrain through Capy preview, a tunnel, or public proxy. Pinned QM binds host interfaces, so `scripts/start qm` first runs `scripts/lockdown`: idempotent sudo `iptables` and `ip6tables` INPUT rules reject eth0 TCP 8081/8097/8113/8129 while retaining lo and docker0. These rules are not reboot-persistent; each later `scripts/start qm` reinstalls them before launching QM. `scripts/stop` intentionally leaves them in place; inspect firewall rules before changing network topology.

Before Telegram cutover, verify the Mac OpenClaw poller and any other process using the same bot token are stopped. Then create `stage/credentials/telegram-cutover-approved` with mode 0600 (`install -m 0600 /dev/null "$HOME/.capy/work/hackathon-runtime/stage/credentials/telegram-cutover-approved"`) and run `scripts/start openclaw`. The script requires both this approval and the private plugin-prepared marker, starts `gateway run` for the `hackathon` profile on its verified port `30650` with an explicit loopback bind, and refuses if another process already owns the port. The approval marker is a human acknowledgement, **not** a distributed Telegram lock; a 409 `getUpdates` conflict means another poller exists. `scripts/start all` requires both markers and is not a rehearsal command. For rollback, `scripts/stop openclaw`, verify the cloud poller is gone, and only then restart the Mac poller; reconcile cloud-side QM/GBrain writes before enabling Mac writers.

`scripts/stop [db|qm|gbrain|openclaw|all]` preserves state; `scripts/status` reports listeners/sessions without printing secrets. GBrain/OpenClaw run in named tmux sessions and write private mode-0600 logs under `stage/logs/`; those logs can contain sensitive data, so never copy or commit them. QM uses its own supervisor (`scripts/dev-instance.sh status` from the pinned checkout) and private pool. Do not remove its database Docker volume as part of normal shutdown.

## JEV decisions

JEV is TypeSafe's hosted System One model, not a local background service. `scripts/install` pins the official `typesafe-sdk==0.7.2`; the similarly named third-party `jev-cli` is not part of this deployment. Put the API key from 1Password in the machine's secure `TYPESAFE_API_KEY` environment variable, never a file in Git. Run a real, synthetic hosted evaluation without printing the key or answer content:

```bash
~/.capy/work/hackathon-runtime/tools/typesafe-sdk/bin/python jev/smoke.py
```

The smoke test makes one API call and may incur usage charges. A new Capy project machine does not inherit a thread-scoped variable: configure the same variable at project scope or securely supply it to that thread. This installs and proves the decision model; integration into a particular QM/OpenClaw workflow requires a separate design.

## Optional authenticated QM preview

Never expose port 8129 directly: its local dev-admin bypass grants admin access to loopback callers, including an unauthenticated preview proxy. For an attended browser demo, `scripts/preview-gate` runs pinned Caddy on host loopback port 8188, requires HTTP Basic Auth for every route, checks the exact public HTTPS origin before rewriting it to QM's local origin, rejects cross-site subresource requests, and strips the proxy password header before forwarding. The username is `qm-demo`. The password must be unique, random, 20–72 printable ASCII characters, supplied through a secure `QM_PREVIEW_PASSWORD` environment variable; the script hashes it into private mode-0600 `stage/credentials/preview.Caddyfile`. Neither the password nor its hash goes in Git or the preview URL. Treat this as a temporary admin gate, not multi-user authentication.

Before the first preview publication, put `https://preview.invalid` in private mode-0600 `stage/credentials/preview-origin`, launch `scripts/preview-gate`, and expose **only** port 8188 through Capy's port preview. Replace `preview-origin` with the exact HTTPS origin returned by that preview, stop the Caddy container (`docker stop qm-preview-gate`), and relaunch the gate so QM's own asset requests pass the origin check. Verify that anonymous `/` and `/admin/` requests get HTTP 401, authenticated requests render both pages, and foreign-origin requests get HTTP 403 before sharing the URL. The proxy binds only `127.0.0.1`; it does not change the firewall rules for QM's raw ports. The gate starts QM and its database when the preview relaunches after machine sleep; GBrain and the Telegram poller still require an attended `scripts/start all` after confirming the Mac poller is off. If the Docker gate survives sleep without its launcher rerunning, authenticated visitors see 502 until `scripts/start qm` restores the upstream. Stop the gate after the demo and remove the secure environment variable when no longer needed.

**Capy cloud lifecycle:** idle sleep stops detached QM, GBrain, and OpenClaw processes. This is not a 24/7 deployment. In a later Capy session, check `scripts/status`, confirm the Mac Telegram poller is still off, then run `scripts/start` to bring the host services back. Do not assume a sleeping machine continuously polls Telegram; if continuous availability matters, move to a separately supervised always-on host. The PostgreSQL container may survive ordinary process shutdown but should still be checked.

Validation here includes shell syntax, locked OpenClaw and JEV dependency installation, a hosted JEV typed-choice evaluation, pinned upstream source checks, a cloud Telegram-to-QM memory save/retrieval, the repo-managed cloud service restart, and anonymous/authenticated/browser checks of the optional HTTPS preview. An isolated fresh Capy VM also ran the pinned install and private restore, then served PostgreSQL, GBrain, QM core, and QM portal successfully without starting OpenClaw. Its copied backup initially had two stale rebuildable plugin symlinks, which were removed before restoring; the cloud source backup has since been cleaned and its 7,215 file hashes match the symlink-free Mac snapshot. The service restart avoids a collision with a Capy-owned link-local listener sharing GBrain's port by checking the expected bind address. Restored OAuth and Telegram cutover have **not** been tested on that second VM; do not start a second Telegram poller during rehearsal.
