# AI Skillz

Agent skills for planning and operating AI work.

This repo follows the same broad layout as `mattpocock-skills`: skills live under bucket folders in `skills/`, each skill owns a `SKILL.md`, and optional `agents/openai.yaml` files provide UI metadata and invocation policy.

## Quickstart

List available skills:

```bash
./scripts/list-skills.sh
```

Symlink the skills into local harness directories for development:

```bash
./scripts/link-skills.sh
```

## Skills

### Engineering

- **[eval-planner](./skills/engineering/eval-planner/SKILL.md)** - Conversationally create and maintain eval, safety, quality, autonomy-readiness, progress, and optional tracker plans.
