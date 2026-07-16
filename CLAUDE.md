Skills are organized into bucket folders under `skills/`:

- `engineering/` - stable code and AI engineering workflows
- `productivity/` - stable general workflow tools
- `misc/` - useful but not promoted
- `personal/` - tied to a personal setup
- `in-progress/` - drafts and placeholders
- `deprecated/` - no longer used

Every skill must contain `SKILL.md`. Prefer adding `agents/openai.yaml` with user-facing metadata and invocation policy.

Promoted buckets are `engineering/` and `productivity/`. Promoted skills should appear in the top-level `README.md` and their bucket `README.md`. Draft skills in `in-progress/` should appear only in `skills/in-progress/README.md` until they graduate.

Use `scripts/list-skills.sh` to list every skill in the repo. Use `scripts/link-skills.sh` to symlink repo skills into local harness skill directories for development.

