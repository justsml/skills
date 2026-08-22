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

For a mid-flight request, match the symptom to the phase that owns it rather than defaulting to the next step in sequence:

- "The scorer disagrees with humans, flip-flops, or seems gameable" → `phases/validate-scorer.md`, not trace mining or optimization.
- "We don't know what's failing yet, or only have production/experiment logs" → `phases/mine-traces.md`.
- "We know the failure but have no cases that reproduce it" → `phases/build-dataset.md`.
- "We have cases and a metric but no way to score them automatically" → `phases/build-scorer.md`.
- "We need a trustworthy number for where things stand today" → `phases/run-regressions.md`.
- "The metric itself is questionable, or a new risk or claim surfaced" → `phases/design.md`.
- "The metric and held-out evaluation are trusted, and we want the score to move" → `phases/optimize.md`.

When a symptom could plausibly map to more than one phase, pick the earliest one in the sequence above — fixing the metric or scorer before searching against it is cheaper than discovering the search was pointed at a broken instrument.

## Detect the platform

Before opening a phase's platform notes, work out which platform, if any, actually applies. Do not ask the user first; check the environment.

1. **Env keys.** Check for platform-scoped variables: `BRAINTRUST_API_KEY` (Braintrust); `CONFIDENT_API_KEY` (DeepEval/Confident AI); `INSPECT_EVAL_MODEL` (Inspect AI); `LANGSMITH_API_KEY` or `LANGCHAIN_API_KEY` with `LANGCHAIN_TRACING_V2` (LangSmith); `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, or `LANGFUSE_BASE_URL` (Langfuse); `PHOENIX_API_KEY` or `PHOENIX_COLLECTOR_ENDPOINT` (Phoenix).
2. **CLIs present and linked.** Check `PATH` for `braintrust`, `deepeval`, `inspect`, `langfuse-cli`, `phoenix`, `promptfoo`, or `gepa`. A present CLI is a weaker signal than one that is also authenticated — a quick `<cli> whoami`, `<cli> --version` plus a config file, or an existing login/session file confirms it is actually linked rather than just installed.
3. **Dependency manifests and config files.** Scan `package.json`, `pyproject.toml`, `requirements.txt`, or lockfiles for `braintrust`, `deepeval`, `inspect-ai`, `langsmith`, `langfuse`, `arize-phoenix`, `promptfoo`, or `gepa`. A `promptfooconfig.yaml`/`.yml` at the repo root is a strong Promptfoo signal on its own.
4. **MCP servers configured.** Check `.mcp.json`, project or user Claude settings, and the current tool list for a connected MCP server matching one of these platforms (e.g. a `braintrust` or `langfuse` MCP server or tool prefix).

Treat these as corroborating signals, not a vote: a linked CLI or configured MCP server outweighs a stray env key left over from another project. When exactly one platform is well-supported by the evidence, use it and name the signal that justified it (e.g. "using Langfuse — `LANGFUSE_SECRET_KEY` is set and `langfuse` is a direct dependency"). When multiple platforms are equally well-supported, say so and ask which one applies rather than guessing.

When no platform is supported by any signal, that is a normal outcome, not a blocker: proceed with plain scripts, the repository's existing test runner, and the markdown decision record below, and say that no platform was detected rather than asking the user to name one. Only ask when the evidence is genuinely ambiguous between two or more platforms. Never fabricate a signal or silently default to a platform absent from the environment.

## Work proactively

Do not wait until completion to surface what you notice. As each phase produces evidence, call out interesting patterns immediately — a slice that dominates failures, a metric that moved for the wrong reason, a scorer that agrees suspiciously often with one candidate, a dataset skew, a cost outlier. Surface it as soon as it's visible, not batched into a final report.

Before starting a phase, verify its prerequisites are actually met rather than assuming the happy path: a dataset exists and is reachable, credentials for the detected platform are valid, the held-out set is still frozen, the baseline result is recent enough to compare against. If a prerequisite is missing or stale, say so and propose the fix before burning a run on it.

After finishing a phase, suggest the likely next step from the sequence in **Route the work** rather than stopping silently — but stop short of starting it uninvited when it spends money, mutates shared state, or the user hasn't indicated they want the full pipeline run end to end.

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

Keep tuning examples separate from the held-out set. This is a hard rule, not a preference: optimization must never read the held-out set's cases or labels, directly or through a scorer trained or tuned on them. If it did, the resulting result is invalid and must be discarded and rerun against a clean split, not just treated as weaker evidence. Record dataset, prompt, model, tool, and scorer versions for every result used in a decision. Treat critical safety, privacy, authorization, and irreversible-action failures as gates rather than averages.

The `## Experiments` and `## Decisions` tables are a working log, not an archive. Once a table exceeds roughly 15-20 rows, move superseded or no-longer-actionable rows to `.scratch/evals/<short-name>/archive.md` and keep only the current baseline, the active candidates, and the most recent decisions inline. A decision record that nobody can scan in under a minute has stopped doing its job.

## Completion

Finish when the current decision is stated, its evidence is reproducible, remaining uncertainty is explicit, the held-out set is confirmed frozen and unexposed to the accepted candidate's tuning, and the next action has an owner or the program has a justified stop decision.
