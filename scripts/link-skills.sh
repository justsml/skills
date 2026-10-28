#!/usr/bin/env bash
set -euo pipefail

# Development helper: symlink every skill in this repo into common local
# harness directories. Re-run after adding, moving, or renaming skills.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DESTS=("$HOME/.claude/skills" "$HOME/.agents/skills" "$HOME/.codex/skills")
if [ "$#" -gt 0 ]; then
  DESTS=()
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --dest)
        [ "$#" -ge 2 ] && [ -n "$2" ] || { echo 'error: --dest needs a path' >&2; exit 2; }
        DESTS+=("$2")
        shift 2
        ;;
      --help|-h)
        echo 'Usage: link-skills.sh [--dest DIRECTORY ...]'
        echo 'Defaults to user Claude, Agents and Codex skill directories. Refuses conflicting destinations.'
        exit 0
        ;;
      *) echo "error: unknown argument $1" >&2; exit 2 ;;
    esac
  done
fi

names=()
srcs=()
while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  names+=("$(basename "$src")")
  srcs+=("$src")
done < <(find "$REPO/skills" -name SKILL.md -not -path '*/node_modules/*' -not -path '*/deprecated/*' -print0)

# Preflight every destination before making changes. A collision is never
# permission to replace another installation, even if it is a dangling link.
for DEST in "${DESTS[@]}"; do
  if [ -L "$DEST" ] || { [ -e "$DEST" ] && [ ! -d "$DEST" ]; }; then
    echo "error: $DEST must be a real directory" >&2
    exit 1
  fi
  for i in "${!names[@]}"; do
    target="$DEST/${names[$i]}"
    if [ -L "$target" ] && [ "$(readlink "$target")" = "${srcs[$i]}" ]; then
      continue
    fi
    if [ -e "$target" ] || [ -L "$target" ]; then
      echo "error: refusing to replace $target; move or back it up explicitly first" >&2
      exit 1
    fi
  done
done

for DEST in "${DESTS[@]}"; do
  mkdir -p -- "$DEST"
  for i in "${!names[@]}"; do
    target="$DEST/${names[$i]}"
    if [ -L "$target" ] && [ "$(readlink "$target")" = "${srcs[$i]}" ]; then
      continue
    fi
    # No force: a target created after preflight must also survive.
    ln -s -- "${srcs[$i]}" "$target"
    echo "linked ${names[$i]} -> ${srcs[$i]} ($DEST)"
  done
done

