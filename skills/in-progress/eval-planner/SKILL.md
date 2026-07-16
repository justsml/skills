---
name: eval-planner
description: Conversationally create, update, and operate a comprehensive evaluation analysis and plan for AI features, prompts, agents, model migrations, retrieval workflows, or quality investigations. Use when the user wants an eval plan, lifecycle planning, progress tracking tables, readiness/risk review, or optional ticket creation in any available tracker through MCP tools, CLIs, or local files.
---

# Eval Planner

Turn a fuzzy AI quality goal into a living evaluation plan: current analysis, hypotheses, measures, datasets, scorers, work breakdown, progress tables, risks, decisions, and optional tracker tickets.

This is a user-invoked orchestration skill. Keep the conversation collaborative and update the planning artifact as the plan changes.

## Command Surface

Support explicit subcommands when the user provides them. If no subcommand is provided, infer the nearest lifecycle action.

- `start` / `analyze`: Create a new evaluation analysis and plan.
- `update`: Update the plan from new findings, test results, implementation progress, or changed requirements.
- `status`: Produce a concise status readout from the current plan and tracker state.
- `review`: Audit the plan for gaps, weak metrics, unclear acceptance criteria, missing datasets, scorer risk, or blocked work.
- `tickets`: Turn approved plan rows into tickets in an available system.
- `sync`: Reconcile ticket status, plan progress, and decisions.
- `close`: Produce a final summary, outcomes table, remaining risk, and follow-up recommendations.

Treat command names as conveniences, not a strict parser. Users may say "make me a plan", "refresh the eval plan", "turn this into Linear issues", or "where are we?"

## Default Artifact

Prefer updating an existing user-named file. If none exists, create a Markdown artifact at:

```text
.scratch/eval-planner/<short-slug>/plan.md
```

Use this structure:

```markdown
# <Evaluation Plan Name>

## Goal

## Current Analysis

## Assumptions And Open Questions

| ID | Question | Owner | Needed By | Status |
| --- | --- | --- | --- | --- |

## Evaluation Design

| Claim | Metric | Dataset / Cases | Scorer | Threshold | Notes |
| --- | --- | --- | --- | --- | --- |

## Work Plan

| ID | Work Item | Outcome | Blocked By | Owner | Status | Tracker |
| --- | --- | --- | --- | --- | --- | --- |

## Progress

| Date | Change | Evidence | Decision / Impact |
| --- | --- | --- | --- |

## Risks

| Risk | Likelihood | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- |

## Decisions

| Date | Decision | Rationale | Revisit Trigger |
| --- | --- | --- | --- |
```

## Start / Analyze

1. Identify the target behavior: product surface, prompt, agent, model call, retrieval path, or workflow.
2. Ask only blocking questions. If the user gave enough context to draft, draft first and mark uncertainties as open questions.
3. Inspect relevant local files, docs, prompts, evals, datasets, and tests when available.
4. Write the first plan artifact with the tables above.
5. End with the next 3-5 concrete actions and which can be ticketed.

Good analysis separates:

- Product claims: what must be true for users or operators.
- Evaluation design: how those claims will be measured.
- Implementation work: changes needed to make the eval possible.
- Evidence: logs, traces, examples, human review, regression tests, benchmark results.

## Update / Sync / Status

When updating, preserve history instead of replacing it.

- Append new rows to `Progress`.
- Update current `Status` cells in `Work Plan`.
- Add decisions to `Decisions`; do not bury them in prose only.
- Move resolved assumptions out of `Open Questions` or mark them `closed`.
- Re-check blocked work and note the smallest unblocker.

For status readouts, report:

- Overall state: `drafting`, `building`, `running`, `reviewing`, `blocked`, or `complete`.
- Completed since last update.
- Current blockers and owners.
- Next frontier work.
- Any metric, dataset, or scorer risk that could invalidate the plan.

## Review

Audit the plan for evaluation failure modes:

- Metrics do not match the product claim.
- Dataset is too small, stale, synthetic-only, or missing adversarial cases.
- Scorer is uncalibrated, underspecified, or likely to reward style over correctness.
- Thresholds are arbitrary or impossible to interpret.
- Work items are horizontal chores instead of verifiable slices.
- Acceptance criteria cannot be checked by a fresh agent.
- The plan lacks a rollback or decision rule for bad results.

Prefer specific fixes over abstract critique. Update the artifact with recommended changes when the user asks you to apply the review.

## Tickets

Only create or update external tickets after the user approves the breakdown or explicitly asks you to publish.

Choose the best available ticket system in this order:

1. An MCP/app connector already available in the session.
2. A repo-supported CLI already installed and authenticated.
3. The platform implied by existing repo metadata.
4. Local Markdown files under the eval plan directory.

Ticket each vertical slice from `Work Plan`, not each table section. Good tickets produce evidence:

```markdown
## Outcome

<What becomes measurable, runnable, or reviewable when this is done.>

## Acceptance Criteria

- [ ] <Evidence-producing criterion>
- [ ] <Regression or quality gate>

## Eval Context

- Plan: <path or URL>
- Claim / metric: <reference>
- Blocked by: <ticket refs or "None">
```

After publishing, write ticket IDs or URLs back into the `Tracker` column.

## Close

Close by producing a short final report and updating the artifact:

- Outcomes by metric and threshold.
- What shipped or changed.
- Known residual risk.
- Follow-up work worth ticketing separately.
- Decision: proceed, hold, revise, or abandon.
