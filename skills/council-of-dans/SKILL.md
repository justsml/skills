---
name: council-of-dans
description: "Run independent, task-matched expert attempts, select a base, and synthesize the strongest result."
disable-model-invocation: true
---

# Council of Dans

Run independent attempts at the same task, judge them against a task-specific rubric, choose the strongest base, graft in compatible strengths, and verify the synthesis.

## Inputs

Honor user-supplied knobs. Infer the rest:

- `N`: number of candidates
- `personas`: required, excluded, or user-defined lenses
- `concurrency`: maximum simultaneous subagents
- `reasoning`: effort by phase or persona
- `judge`: `parent`, `subagent`, or `both`
- `isolation`: worktrees, separate directories, or read-only proposals
- `artifacts`: output and synthesis-note paths

Default `N` to the number of high-confidence, materially useful personas, bounded to 4–6. Do not pad the council with weak matches. If fewer than four personas are useful, use the smaller panel and state why. Ask only when a missing knob would materially change the result; otherwise proceed with recorded assumptions.

## Select the council

Each candidate owns the complete task. Its persona changes what it notices, what it distrusts, and what it optimizes. Give the role enough theatrical force to pull the candidate away from the most obvious solution, but keep its mandate concrete.

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

The name should activate a worldview. The mandate keeps it useful. Tell candidates to stay in character while still delivering the whole artifact. Exclude personas whose likely contribution substantially overlaps another panelist. Record one sentence per selected persona explaining the distinct solution pressure it adds; those sentences determine `N`.

Use one capable model across candidates unless the user or environment specifies otherwise. For coding candidates, prefer low reasoning effort; raise it only when measured complexity warrants it. For planning, architecture, and judging, prefer medium or high reasoning effort.

## Frame

Before spawning:

1. Name the complete artifact each candidate must produce.
2. Write 3–6 task-specific, gradeable criteria.
3. Select the personas and derive `N`.
4. Choose safe isolation. Candidates that write files need separate worktrees or directories; candidates must not edit the same files concurrently.
5. Record the concurrency and reasoning settings.

The frame is complete when every candidate can receive the same task contract, one distinct persona, and one isolated output location.

## Fan out

Launch an initial wave of at most four parallel subagents, further limited by available system slots and resources. Each receives:

- the common task and grounding context;
- one persona and its emphasis;
- its isolated output path;
- instructions to produce the complete artifact plus a short rationale naming alternatives considered and rejected.

Queue remaining candidates as slots free up. After the first wave, increase the concurrency cap to at most eight only when the environment supports it and observed orchestration overhead, memory, CPU, tool contention, and failure rate indicate that doubling is safe. Otherwise retain or reduce the cap. Never exceed platform limits or sacrifice isolation to reach a target number.

Proceed after a candidate dropout when enough independent work remains to compare; record the dropout.

## Judge and pick

Wait for all candidates before judging. Read every artifact and rationale end to end, then score each criterion rather than choosing by familiarity or polish.

When `judge` includes a subagent, use a neutral, read-only judge that sees candidates by path label and receives the rubric but not the parent's preference. Run it only after candidate writes finish. Compare its verdict with the parent's scoring and resolve disagreements from the evidence.

Choose the base that best satisfies the rubric and remains easiest to extend without breaking its invariants. Break close ties toward the smaller coherent surface.

## Synthesize

Revisit each losing candidate once. Graft only ideas that improve the base without introducing a second mental model. Rework them into the base instead of pasting mechanically.

- Convergence is evidence for the shared shape; no graft is required.
- Sharp divergence usually means the frame was underspecified; reframe and rerun instead of averaging incompatible answers.
- Preserve user-owned and concurrent filesystem changes throughout synthesis.

## Verify and report

Verify the synthesized artifact through the task's real public seam. A council does not weaken the normal proof bar.

Return one synthesized artifact and a concise synthesis note containing:

- selected personas, `N`, concurrency, and reasoning settings;
- the chosen base and criterion-level reason;
- grafts and their source candidates;
- notable rejections and dropouts;
- verification performed and result.
