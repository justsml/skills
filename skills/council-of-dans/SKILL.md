---
name: council-of-dans
description: "Run independent, task-matched expert attempts, select a base, and synthesize the strongest result."
disable-model-invocation: true
---

# Council of Dans

Run independent solution families against the same task, judge them with a task-specific rubric, choose the strongest base, graft compatible strengths, and verify the synthesis.

## Inputs

Honor user-supplied knobs. Infer the rest:

- `N`: number of candidates
- `personas`: required, excluded, or user-defined lenses
- `concurrency`: maximum simultaneous subagents
- `reasoning`: effort by phase or persona
- `judge`: `parent`, `subagent`, or `both`
- `isolation`: worktrees, separate directories, or read-only proposals
- `artifacts`: output and synthesis-note paths

Start with `N = 2` unless the user supplies a panel size. Treat a user-supplied size, personas, and concurrency as authoritative when they are safe and the environment supports them. Ask only when a missing knob would materially change the result. Record inferred settings.

## Define independent approaches

Each candidate owns the complete task and tests a different solution hypothesis. Define each candidate by at least one explicit source of independence:

- a different architecture or decomposition;
- a different governing constraint or tradeoff;
- a different hypothesis about the cause or best route;
- a materially different compatibility or migration strategy.

Persona wording alone does not make candidates independent. Use a persona only as a lens within a named solution family. For each candidate, record one sentence explaining what decision it could change. If two briefs would likely produce the same design, combine them or drop one.

Use these lenses only when they sharpen a distinct approach:

Start from these general lenses and retain only strong matches:

| Persona | Useful when |
|---|---|
| Systems Architect | Defends boundaries, invariants, interfaces, migration paths, and long-term coherence |
| Detail Detective | Hunts local correctness bugs, edge cases, state transitions, integration gaps, and weak verification |
| Product Visionary | Reimagines the user workflow, discoverability, ergonomics, and compatibility from the user's seat |
| Doomsayer | Assumes the rollout goes wrong and exposes failure modes, hidden costs, complexity, and irreversible choices |
| Ruthless Minimalist | Deletes concepts until only the smallest complete, legible solution remains |
| Genius Inventor | Rejects the obvious framing and searches for a surprising decomposition, combination, or route to the outcome |
| Battle-scarred Operator | Distrusts designs that ignore deployment, observability, recovery, maintenance, resource limits, or day-two use |

Add task-specific characters only when the task gives them something distinct to find. Examples include the Security Paranoid, Privacy Zealot, Performance Wizard, Data Modeler, Algorithm Specialist, Accessibility Advocate, Test Saboteur, or a sharp domain expert. Use a Clean-slate Radical only when redesign is genuinely in scope. That candidate must label compatibility breaks, migration work, data-loss risk, and irreversible choices.

The name should activate a worldview. The mandate keeps it useful. Tell candidates to stay in character while still delivering the whole artifact.

Use one capable model across candidates unless the user or environment specifies otherwise. For coding candidates, prefer low reasoning effort; raise it only when measured complexity warrants it. For planning, architecture, and judging, prefer medium or high reasoning effort.

## Frame

Before spawning:

1. Name the complete artifact each candidate must produce.
2. Write 3–6 task-specific, gradeable criteria.
3. Write two independent solution-family briefs and explain the decision value of each.
4. Choose safe isolation. Candidates that write files need separate worktrees or directories; candidates must not edit the same files concurrently.
5. Record the concurrency and reasoning settings.

The frame is complete when every candidate can receive the same task contract, one distinct solution-family brief, and one isolated output location.

## Fan out

Launch the initial two candidates, limited by available system slots and resources. Each receives:

- the common task and grounding context;
- one solution hypothesis and any useful persona lens;
- its isolated output path;
- instructions to produce the complete artifact plus a short rationale naming alternatives considered and rejected.

After the first two candidates finish, name any unresolved decision that another independent approach could settle. Add one candidate only when its brief tests that uncertainty and could change the selected base or synthesis. Stop when candidates converge, the rubric separates them, or another brief would repeat an existing solution family. Never exceed a user-supplied panel size or platform limits, and never sacrifice isolation to reach a target number.

If a candidate drops out, record it and decide whether the remaining artifacts still represent at least two materially different approaches. Proceed when they do. Replace the candidate when they do not and another run is safe.

## Judge and pick

Wait for all candidates before judging. Read every artifact and rationale end to end, then score each criterion rather than choosing by familiarity or polish.

When `judge` includes a subagent, use a neutral, read-only judge that sees candidates by path label and receives the rubric but not the parent's preference. Run it only after candidate writes finish. Compare its verdict with the parent's scoring. When they disagree, resolve it criterion by criterion: re-read the specific artifacts against the specific criterion each verdict disputed, and let that re-read decide it rather than deferring to either party's overall impression. If the re-read is still genuinely ambiguous on a criterion that changes the pick, say so and choose the base that is safer to extend rather than guessing.

Choose the base that best satisfies the rubric and remains easiest to extend without breaking its invariants. Break close ties toward the smaller coherent surface.

## Synthesize

Revisit each losing candidate once. Graft only ideas that improve the base without introducing a second mental model. Rework them into the base instead of pasting mechanically.

- Convergence is evidence for the shared shape; no graft is required.
- Sharp divergence usually means the frame was underspecified; reframe and rerun instead of averaging incompatible answers.
- Preserve user-owned and concurrent filesystem changes throughout synthesis.

## Verify and report

Verify the synthesized artifact through the task's real public seam. A council does not weaken the normal proof bar.

Return one synthesized artifact and a concise synthesis note containing:

- solution families, personas, `N`, concurrency, reasoning settings, and why each candidate had decision value;
- expansion or stop decision after the initial pair;
- the chosen base and criterion-level reason;
- grafts and their source candidates;
- notable rejections and dropouts;
- verification performed and result.
