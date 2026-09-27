#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO_RUNTIME_ROOT="${DEMO_RUNTIME_ROOT:-$HOME/.capy/work/hackathon-runtime/stage}"
[[ "$DEMO_RUNTIME_ROOT" = /* && "$DEMO_RUNTIME_ROOT" != "$REPO_ROOT"* ]] || {
  echo 'DEMO_RUNTIME_ROOT must be an absolute path outside this repository' >&2; exit 1;
}
source "$REPO_ROOT/versions.env"
DB_NAME=qm-dev-postgres
QM_SOURCE="$DEMO_RUNTIME_ROOT/qm"
GBRAIN_SOURCE="$DEMO_RUNTIME_ROOT/../tools/gbrain"
CLAW_STATE="$DEMO_RUNTIME_ROOT/openclaw"
CLAW_PACKAGE="$CLAW_STATE/npm"
GBRAIN_HOME="$DEMO_RUNTIME_ROOT/gbrain-home"
QM_POOL_STORE="$DEMO_RUNTIME_ROOT/qm-pool"
QM_DEV_ENV="$DEMO_RUNTIME_ROOT/credentials/qm.env"
GBRAIN_SESSION=hackathon-demo-gbrain
CLAW_SESSION=hackathon-demo-openclaw
require() { command -v "$1" >/dev/null || { echo "Missing prerequisite: $1" >&2; exit 1; }; }
require_private() {
  [[ -f "$1" ]] || { echo "Missing private file: $1" >&2; exit 1; }
  [[ "$(stat -c %a "$1")" = 600 ]] || { echo "Private file must have mode 0600: $1" >&2; exit 1; }
}
running() { [[ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null || true)" = true ]]; }
existing() { docker container inspect "$1" >/dev/null 2>&1; }
session() { tmux has-session -t "=$1" 2>/dev/null; }
listening() {
  ss -H -ltn "( sport = :$1 )" | awk -v address="${2:-127.0.0.1}" -v port="$1" \
    '$4 == address ":" port { found = 1 } END { exit !found }'
}
