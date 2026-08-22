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
- **[eval-planner](./skills/eval-planner/SKILL.md)** - Coordinate a complete eval program and its decision record.
- **[eval-design](./skills/eval-design/SKILL.md)** - Design datasets, metric bundles, slices, and release gates.
- **[eval-build-dataset](./skills/eval-build-dataset/SKILL.md)** - Curate versioned evaluation cases with protected splits.
- **[eval-build-scorer](./skills/eval-build-scorer/SKILL.md)** - Implement auditable deterministic, judge, or human scorers.
- **[eval-validate-scorer](./skills/eval-validate-scorer/SKILL.md)** - Calibrate and stress-test learned evaluators.
- **[eval-run-regressions](./skills/eval-run-regressions/SKILL.md)** - Implement reproducible candidate comparisons and CI gates.
- **[eval-mine-traces](./skills/eval-mine-traces/SKILL.md)** - Find failure clusters and regression cases in traces.
- **[eval-optimize](./skills/eval-optimize/SKILL.md)** - Tune prompts and agent components against protected evals.
- **[unslop](./skills/unslop/SKILL.md)** - Remove AI writing tells while preserving meaning and voice.
