# AI Skillz

Agent skills for planning and operating AI work.

Each skill is a directory directly under `skills/` with its own `SKILL.md`, and optional `agents/openai.yaml` files provide UI metadata and invocation policy.

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

- **[council-of-dans](./skills/council-of-dans/SKILL.md)** - Run independent, persona-driven attempts at a task and synthesize the strongest result.
- **[eval-expert](./skills/eval-expert/SKILL.md)** - Coordinate a complete eval program — design, datasets, scorers, regressions, trace mining, and optimization — from one decision record.
- **[unslop](./skills/unslop/SKILL.md)** - Remove AI writing tells while preserving meaning and voice.
