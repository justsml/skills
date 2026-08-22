Skills live directly under `skills/`, one directory per skill, with no bucket folders.

Every skill must contain `SKILL.md`. Prefer adding `agents/openai.yaml` with user-facing metadata and invocation policy.

Every skill should appear in the top-level `README.md`.

Use `scripts/list-skills.sh` to list every skill in the repo. Use `scripts/link-skills.sh` to symlink repo skills into local harness skill directories for development.

## Agent skills

### Issue tracker

Issues and specs are tracked in this repository's GitHub Issues. See `docs/agents/issue-tracker.md`.

### Triage labels

The default five-label triage vocabulary is used. See `docs/agents/triage-labels.md`.

### Domain docs

Domain documentation uses the single-context layout. See `docs/agents/domain.md`.
