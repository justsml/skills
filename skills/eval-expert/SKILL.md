---
name: eval-expert
description: Coordinate a measured evaluation program for an AI feature or agent. Use when the user asks for evaluation design, datasets, scorers, scorer validation, regressions, trace-based failure analysis, optimization backed by measurement, or one maintained eval plan across those activities. Do not use for one-off prompt rewrites, ordinary unit tests, or small AI changes unless the user asks for metrics, comparison, or regression coverage.
---

# Eval expert

Keep one decision record for the evaluation program and work each phase from its own file below.

## Operating contract

Enter only when the request needs measured evidence about AI behavior. Identify the release, tuning, or diagnosis decision before doing phase work. If the user asks for a small implementation or prompt edit without measurement or regression coverage, handle it directly without this skill.

Authorized work includes inspecting local evidence, maintaining the evaluation record, curating cases, implementing eval-only scorers and runners, running approved local evaluations, and analyzing their results. Limit changes to evaluation artifacts and the explicitly requested AI component. Treat production code, deployment, provider settings, shared datasets, and release controls as outside the contract unless the user authorizes that change.

Ask before a paid run, hosted upload, networked action that sends project data, destructive dataset rewrite, production mutation, or release-state change. Credential or platform detection establishes availability, not permission.

Every phase must leave the decision record with its result, evidence, uncertainty, and next route. Stop when the requested phase meets its completion condition, a required input is missing, approval is required, evidence cannot support the decision, or the next phase would expand the user's request.

Non-goals include general AI implementation, one-off prompt polishing, ordinary test writing, provider migration, and production incident response without an evaluation question.

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

If two routes remain plausible and choosing one would change the artifact, spend, permissions, or evidence needed, ask one focused question naming that difference. Otherwise take the earlier route and record the assumption.

## Detect the platform

Before opening platform notes, determine which platform applies and report three independent states for each candidate:

| State | Evidence | Meaning |
| --- | --- | --- |
| Installed | repository dependency, config, executable, or connected tool | The platform can be used from this environment. |
| Authenticated | local session evidence or an approved identity check | An account connection appears usable. |
| Authorized for current data | explicit user approval or a repository policy that covers the named dataset, traces, prompts, outputs, and scores | The current material may be sent to that platform. |

Check evidence in this order:

1. Inspect repository-local dependencies, lockfiles, call sites, eval config, scripts, and project MCP config. This evidence takes precedence because it belongs to the current project.
2. Check relevant executables and local project configuration without making network calls.
3. Check platform credential variables for presence only. Never print, hash, partially reveal, or persist their values.
4. Treat user-global config, login files, and unrelated MCP tools as weak evidence. They may be stale or belong to another project.

Do not run `whoami`, account queries, or other networked identity checks unless the operating contract or the user's request authorizes that network action. A credential variable or saved login can support `authenticated: unknown or likely`; only local proof or an approved check can strengthen it.

When one platform has clear repository-local support, select its local integration and report all three states. When several platforms have comparable repository-local support, ask which one owns the evaluation record. When only global credentials or tools exist, report them as stale or unconfirmed candidates and continue with repository scripts. When no platform is supported, proceed with plain scripts and say so.

Detection never authorizes upload. Before sending traces, manifests, datasets, prompts, outputs, scores, or other project data, name the destination and data scope, confirm `authorized for current data: yes`, and obtain approval when the operating contract requires it. Keep private data local when authorization is absent or unclear.

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

Keep tuning examples separate from the held-out set. This is a hard rule, not a preference: optimization must never read the held-out set's cases or labels, directly or through a scorer trained or tuned on them. If it did, the resulting result is invalid and must be discarded and rerun against a clean split, not just treated as weaker evidence. Record dataset, prompt, model, tool, and scorer versions for every result used in a decision. Treat critical safety, privacy, authorization, and irreversible-action failures as gates rather than averages.

The `## Experiments` and `## Decisions` tables are a working log, not an archive. Once a table exceeds roughly 15-20 rows, move superseded rows to `evals/<short-name>/archive.md` and keep only the current baseline, active candidates, and recent decisions inline. Keep generated bulk output in the run-artifact location rather than pasting it into the contract.

## Completion

Finish when the current decision is stated, its evidence is reproducible, remaining uncertainty is explicit, the held-out set is confirmed frozen and unexposed to the accepted candidate's tuning, and the next action has an owner or the program has a justified stop decision.
