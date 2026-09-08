---
name: council-of-dans
description: "Fan one task out to parallel agents, each working under a different priority — Architect, Originalist, Unoriginalist, Radical, Visionary, Pennypincher, Minimalist, Inventor, Operator — then hand back every result. Use for important decisions, complex planning, alternative options, and trade-offs."
---

# Council of Dans

Run the same task in parallel under different priorities, then present what each agent produced.

Scope ends at presenting. What happens next — return all of them, the fastest, the first to clear a rubric, pipe them into another tool, merge them — is the caller's call. Absent an instruction, hand back the set as it is.

## Knobs

- `N`: candidate count. Default 2 when the model invokes this skill, 4 when the user invokes it by name. A user-supplied number wins.
- `personas`: required, excluded, or user-defined lenses.
- `disposition`: what to do with the results.

Pass any other setting the user supplies — worktrees, output paths, models, reasoning effort — through to the candidates verbatim. Ask only when a missing knob changes the result.

## Personas

| Persona | Priority |
|---|---|
| Architect | Boundaries, ownership, contracts, invariants, migration paths |
| Detail Detective | Concrete control and data paths — edge cases, state bugs, integration gaps, weak verification |
| Originalist | Challenges the default framing and the familiar project pattern |
| Unoriginalist | Reuses established patterns, dependencies, and test seams; reads docs and history before inventing |
| Clean-slate Radical | First principles, best end state over smallest migration; names the compatibility breaks and irreversible choices |
| Product Visionary | Starts from the user's workflow — behavior, discoverability, ergonomics |
| Doomsayer | Breaks it before users do — failure modes, hidden costs, unsafe rollouts |
| Ruthless Minimalist | Smallest coherent change that fully satisfies the task |
| Genius Inventor | A non-obvious but implementable mechanism that materially improves the result |
| Battle-scarred Operator | Deployment, observability, recovery, resource limits, day-two ownership |
| Performance Wizard | Speed, memory, throughput; bottlenecks and their tradeoffs |
| Pennypincher | Cost, complexity, dependencies, hidden maintenance |

Add a task-specific persona when the task gives it something distinct to find: Security Paranoid, Privacy Zealot, Data Modeler, Accessibility Advocate, Test Saboteur, a sharp domain expert. Use Clean-slate Radical only when redesign is in scope.

The name supplies the worldview; the brief ties it to the work. Each candidate owns the whole task and does it for real — inspects the repo, makes the change, runs the checks — with the persona as an execution bias, not a writing style.

## Fan out

Give each candidate the same task contract, one persona brief, and its own output location. Two briefs that would produce the same result are one candidate: combine or drop, and record in a sentence what decision each survivor could change.

Start one candidate and add the next only while local resources stay clear, up to `N`; pause on contention and resume when it clears. Candidates that write files never share a directory.

Ask each for its work plus a short rationale naming what it considered and rejected.

## Present

Report the personas and `N` used, each candidate's output and rationale, and any dropout or failure. Keep candidates distinct and attributed — no silent merging, ranking, or dropping.

Then carry out whatever disposition the user asked for.
