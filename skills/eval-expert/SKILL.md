---
name: eval-expert
description: Coordinate a measured evaluation program for an AI feature or agent. Use when the user asks for evaluation design, datasets, scorers, scorer validation, regressions, trace-based failure analysis, optimization backed by measurement, or one maintained eval plan across those activities. Do not use for one-off prompt rewrites, ordinary unit tests, or small AI changes unless the user asks for metrics, comparison, or regression coverage.
---

# Eval expert

Keep one decision record for the evaluation program and work each phase from its own file below.

**Held-out data is never touched by tuning.** Optimization must not read the held-out set's cases or labels, directly or through a scorer trained or tuned on them. A result produced in violation of this is invalid: discard it and rerun against a clean split. It is not weaker evidence.

## Operating contract

- **Enter** only when the request needs measured evidence about AI behavior, and name the release, tuning, or diagnosis decision first. A small implementation or prompt edit with no measurement or regression coverage does not need this skill.
- **Change** only evaluation artifacts and the AI component the user named. Production code, deployment, provider settings, shared datasets, and release controls are out of scope unless the user authorizes the change.
- **Ask first** before a paid run, hosted upload, any networked action that sends project data, a destructive dataset rewrite, a production mutation, or a release-state change. Detecting a credential or platform establishes availability, not permission.

Every phase leaves the decision record with its result, evidence, uncertainty, and next route. Stop when the phase meets its completion condition, a required input is missing, approval is needed, evidence cannot support the decision, or the next phase would expand the request.

## Route the work

Match the symptom to the phase that owns it. Do that phase directly rather than starting at the top of the pipeline:

- "The scorer disagrees with humans, flip-flops, or seems gameable" → `phases/validate-scorer.md`, not trace mining or optimization.
- "We don't know what's failing yet, or only have production/experiment logs" → `phases/mine-traces.md`.
- "We know the failure but have no cases that reproduce it" → `phases/build-dataset.md`.
- "We have cases and a metric but no way to score them automatically" → `phases/build-scorer.md`.
- "We need a trustworthy number for where things stand today" → `phases/run-regressions.md`.
- "The metric itself is questionable, or a new risk or claim surfaced" → `phases/design.md`.
- "The metric and held-out evaluation are trusted, and we want the score to move" → `phases/optimize.md`.
- "The thing being tuned is a prompt, and the loop has stalled" → `prompt-tuning.md`.

For multi-phase work, sequence it as failure discovery, design, dataset construction, scorer implementation, scorer validation, baseline execution, optimization, then held-out confirmation. Re-enter design whenever evidence shows the metric rewards the wrong behavior or misses an important failure.

When a symptom maps to more than one phase, take the earlier one — fixing the instrument is cheaper than discovering the search was pointed at a broken one. If the choice would change the artifact, spend, permissions, or evidence needed, ask one focused question naming that difference; otherwise take the earlier route and record the assumption.

## Detect the platform

Before opening platform notes, report three independent states for each candidate platform:

- **Installed** — a repository dependency, config, executable, or connected tool.
- **Authenticated** — local session evidence, or an approved identity check.
- **Authorized for current data** — explicit user approval, or a repository policy covering this dataset, traces, prompts, outputs, and scores.

Trust repository-local evidence — dependencies, lockfiles, call sites, eval config, scripts, project MCP config — over user-global config, login files, and unrelated MCP tools, which may be stale or belong to another project. Check credential variables for presence only; never print, hash, partially reveal, or persist a value. Do not run `whoami` or other networked identity checks unless the request authorizes that network call: a saved credential supports `Authenticated: unconfirmed`, nothing stronger.

One platform with repository-local support wins. Several with comparable support means asking which owns the evaluation record. Only global credentials means reporting them as unconfirmed and continuing with repository scripts. No platform means plain scripts, and say so.

**Detection never authorizes upload.** Before sending any project data, name the destination and scope and confirm `Authorized for current data: yes`.

## Work proactively

Do not wait until completion to surface what you notice. As each phase produces evidence, call out interesting patterns immediately — a slice that dominates failures, a metric that moved for the wrong reason, a scorer that agrees suspiciously often with one candidate, a dataset skew, a cost outlier. Surface it as soon as it's visible, not batched into a final report.

Before starting a phase, verify its prerequisites rather than assuming the happy path: a dataset exists and is reachable, the required platform state is established, the current data is authorized for the planned destination, the held-out set is still frozen, and the baseline is recent enough to compare against. If a prerequisite is missing or stale, say so and propose the fix before burning a run on it.

After finishing a phase, suggest the likely next step from the sequence in **Route the work** rather than stopping silently — but stop short of starting it uninvited when it spends money, mutates shared state, or the user hasn't indicated they want the full pipeline run end to end.

## Maintain the decision record

Classify artifacts before writing them:

- **Temporary exploration:** disposable notes, probes, and dry-run output. Store them under `.scratch/evals/<short-name>/`. They do not support a release decision and may be deleted.
- **Reviewed evaluation contract:** the current claims, gates, dataset and scorer identities, decisions, and open failures. Prefer the user's existing versioned artifact. Otherwise create `evals/<short-name>/plan.md` so the project can review and version it.
- **Generated run artifacts:** raw outputs, traces, scorer details, and reports tied to a run identity. Store them in the repository's configured artifact location. If none exists, use `evals/<short-name>/runs/<run-id>/` for small, reviewable artifacts or a named local artifact directory for large or sensitive data. Record the path, digest, retention rule, and data classification in the reviewed contract.

Do not leave a decision used for tuning, gating, or release only in `.scratch`. Promote the relevant contract and summarized evidence to the durable record first. Promotion requires a source-to-destination review, stable dataset and scorer identities, and removal or redaction of data that the repository must not version.

Keep the reviewed contract limited to current decisions:

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

Record dataset, prompt, model, tool, and scorer versions for every result used in a decision. Treat critical safety, privacy, authorization, and irreversible-action failures as gates rather than averages.

The `## Experiments` and `## Decisions` tables are a working log, not an archive. Once a table exceeds roughly 15-20 rows, move superseded rows to `evals/<short-name>/archive.md` and keep only the current baseline, active candidates, and recent decisions inline. Keep generated bulk output in the run-artifact location rather than pasting it into the contract.

## Completion

Finish when the current decision is stated, its evidence is reproducible, remaining uncertainty is explicit, the held-out set is confirmed frozen and unexposed to the accepted candidate's tuning, and the next action has an owner or the program has a justified stop decision.
