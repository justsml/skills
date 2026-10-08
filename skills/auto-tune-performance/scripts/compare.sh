#!/usr/bin/env bash
# Bash 3.2+ dispatcher: no packages, downloads, secret loading, or cloud calls.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
# Probe compatibility only. A helper validation failure must never trigger fallback.
if command -v node >/dev/null 2>&1 && node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 20 ? 0 : 1)' >/dev/null 2>&1; then
  exec node "$script_dir/compare.mjs" "$@"
fi
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
  exec python3 "$script_dir/compare.py" "$@"
fi
printf '%s\n' 'ERROR: requires Node 20+ or Python 3.10+; neither compatible runtime is available.' >&2
exit 2
