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

- **[eval-planner](./skills/engineering/eval-planner/SKILL.md)** - Coordinate a complete eval program and its decision record.
- **[eval-design](./skills/engineering/eval-design/SKILL.md)** - Design datasets, metric bundles, slices, and release gates.
- **[eval-build-dataset](./skills/engineering/eval-build-dataset/SKILL.md)** - Curate versioned evaluation cases with protected splits.
- **[eval-build-scorer](./skills/engineering/eval-build-scorer/SKILL.md)** - Implement auditable deterministic, judge, or human scorers.
- **[eval-validate-scorer](./skills/engineering/eval-validate-scorer/SKILL.md)** - Calibrate and stress-test learned evaluators.
- **[eval-run-regressions](./skills/engineering/eval-run-regressions/SKILL.md)** - Implement reproducible candidate comparisons and CI gates.
- **[eval-mine-traces](./skills/engineering/eval-mine-traces/SKILL.md)** - Find failure clusters and regression cases in traces.
- **[eval-optimize](./skills/engineering/eval-optimize/SKILL.md)** - Tune prompts and agent components against protected evals.
