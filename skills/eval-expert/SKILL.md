---
name: eval-expert
description: Coordinate an end-to-end evaluation program for an AI feature or agent. Use when the work spans metric design, dataset curation, scorer implementation and validation, regression execution, trace analysis, and iterative optimization, or when the user wants one maintained eval plan across those activities.
---

# Eval expert

Keep one decision record for the evaluation program and work each phase from its own file below.

## Route the work

- Read `phases/design.md` to turn product claims and risks into datasets, metrics, slices, and decision gates.
- Read `phases/build-dataset.md` to curate versioned development, validation, held-out, and regression cases.
- Read `phases/build-scorer.md` to implement one evidence-producing scorer per metric.
- Read `phases/validate-scorer.md` before a learned scorer can influence tuning, release, or safety decisions.
- Read `phases/run-regressions.md` to make the design executable and compare candidates reproducibly.
- Read `phases/mine-traces.md` when production or experiment traces are the evidence source.
- Read `phases/optimize.md` only after the objective and held-out evaluation are credible.

Do the requested phase directly. For multi-phase work, sequence it as failure discovery, design, dataset construction, scorer implementation, scorer validation, baseline execution, optimization, then held-out confirmation. Re-enter design whenever evidence shows that the metric rewards the wrong behavior or misses an important failure.

## Detect the platform

Before opening a phase's platform notes, work out which platform, if any, actually applies. Do not ask the user first; check the environment.

1. **Env keys.** Check for platform-scoped variables: `BRAINTRUST_API_KEY` (Braintrust); `CONFIDENT_API_KEY` (DeepEval/Confident AI); `INSPECT_EVAL_MODEL` (Inspect AI); `LANGSMITH_API_KEY` or `LANGCHAIN_API_KEY` with `LANGCHAIN_TRACING_V2` (LangSmith); `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, or `LANGFUSE_BASE_URL` (Langfuse); `PHOENIX_API_KEY` or `PHOENIX_COLLECTOR_ENDPOINT` (Phoenix).
2. **CLIs present and linked.** Check `PATH` for `braintrust`, `deepeval`, `inspect`, `langfuse-cli`, `phoenix`, `promptfoo`, or `gepa`. A present CLI is a weaker signal than one that is also authenticated — a quick `<cli> whoami`, `<cli> --version` plus a config file, or an existing login/session file confirms it is actually linked rather than just installed.
3. **Dependency manifests and config files.** Scan `package.json`, `pyproject.toml`, `requirements.txt`, or lockfiles for `braintrust`, `deepeval`, `inspect-ai`, `langsmith`, `langfuse`, `arize-phoenix`, `promptfoo`, or `gepa`. A `promptfooconfig.yaml`/`.yml` at the repo root is a strong Promptfoo signal on its own.
4. **MCP servers configured.** Check `.mcp.json`, project or user Claude settings, and the current tool list for a connected MCP server matching one of these platforms (e.g. a `braintrust` or `langfuse` MCP server or tool prefix).

Treat these as corroborating signals, not a vote: a linked CLI or configured MCP server outweighs a stray env key left over from another project. When exactly one platform is well-supported by the evidence, use it and name the signal that justified it (e.g. "using Langfuse — `LANGFUSE_SECRET_KEY` is set and `langfuse` is a direct dependency"). When multiple platforms are equally well-supported, or none are, say so and ask which platform applies rather than guessing. Never fabricate a signal or silently default to a platform absent from the environment.

## Maintain the decision record

Prefer the user's existing artifact. Otherwise create `.scratch/evals/<short-name>/plan.md` with only the sections that carry current decisions:

```markdown
# <name>

## Target behavior and release decision

## Evaluation contract

| Claim or risk | Dataset slice | Metric or gate | Scorer | Threshold | Evidence |
| --- | --- | --- | --- | --- | --- |

## Experiments

| Candidate | Change | Development result | Held-out result | Cost and latency | Decision |
| --- | --- | --- | --- | --- | --- |

## Open failures and next actions

| Failure cluster | Evidence | Likely cause | Next discriminating test | Owner |
| --- | --- | --- | --- | --- |

## Decisions

| Date | Decision | Evidence | Revisit when |
| --- | --- | --- | --- |
```

Keep tuning examples separate from the held-out set. Record dataset, prompt, model, tool, and scorer versions for every result used in a decision. Treat critical safety, privacy, authorization, and irreversible-action failures as gates rather than averages.

## Completion

Finish when the current decision is stated, its evidence is reproducible, remaining uncertainty is explicit, and the next action has an owner or the program has a justified stop decision.
