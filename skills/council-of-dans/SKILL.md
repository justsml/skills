---
name: council-of-dans
description: "Run independent agents each with a specific focus or priority. From The Architect, The Originalist, The Unoriginalist, The Radical, The Visionary, The Pennypincher, The Minimalist, The Inventor, and The Operator. Consult a range of perspectives on important decisions, complex planning, finding alternative options, and understanding trade-offs."
disable-model-invocation: true
---

# Council of Dans

Fan the same task out to independent agents, each running under a different priority agenda, and hand back what they produced.

The scope of this skill is the fan-out: frame the task, assign distinct lenses, run the work in isolation, and present the results. What happens next — return all of them, return the fastest, feed them to a judge or rubric, pipe them into another tool, pick one, merge them — is the caller's call. Do only what the caller asked for, and when they asked for nothing in particular, return the results as they are.

## Inputs

Honor user-supplied knobs. Infer the rest:

- `N`: number of parallel candidates
- `personas`: required, excluded, or user-defined lenses
- `concurrency`: maximum simultaneous subagents
- `reasoning`: effort by phase or persona
- `isolation`: worktrees, separate directories, or read-only proposals
- `artifacts`: output paths
- `disposition`: what to do with the results once they exist

Start with `N = 3` unless the user supplies a panel size. Treat a user-supplied size, personas, and concurrency as authoritative when they are safe and the environment supports them. Ask only when a missing knob would materially change the result. Record inferred settings.

## Define independent approaches

Each candidate owns the whole task and runs it under a different priority agenda. Define each candidate by at least one explicit source of independence:

- a different architecture or decomposition;
- a different governing constraint or tradeoff;
- a different hypothesis about the cause or best route;
- a materially different compatibility or migration strategy.

Persona wording alone does not make candidates independent. Use a persona as a lens on a named approach. For each candidate, record one sentence explaining what decision it could change. If two briefs would likely produce the same result, combine them or drop one.

Choose only lenses that sharpen a distinct approach:

| Persona | Useful when |
|---|---|
| The Architect | Maps boundaries, ownership, contracts, invariants, and migration paths so the change remains coherent as the codebase evolves |
| Detail Detective | Traces concrete control and data paths to catch edge cases, state bugs, integration gaps, and weak verification |
| Originalist | Challenges the default framing and familiar project patterns to produce a distinct solution grounded in the task and codebase |
| Unoriginalist | Reuses established project patterns, dependencies, and test seams; consults documentation and history before inventing a new abstraction |
| Clean-slate Radical | Rethinks the system from first principles, choosing boundaries, data structures, and algorithms for the best end state rather than the smallest migration |
| Product Visionary | Starts from the user's workflow and reshapes behavior, discoverability, ergonomics, and compatibility around it |
| Doomsayer | Tries to break the change before users do, exposing failure modes, hidden costs, unsafe rollouts, and irreversible choices |
| Ruthless Minimalist | Produces the smallest coherent diff that fully satisfies the task, removing needless concepts, dependencies, and machinery |
| Genius Inventor | Finds a non-obvious but implementable mechanism or decomposition that materially improves the result |
| Battle-scarred Operator | Designs for deployment, observability, recovery, maintenance, resource limits, and day-two ownership |
| Performance Wizard | Optimizes for speed, memory, and throughput, exposing bottlenecks and tradeoffs |
| Pennypincher | Reduces cost, complexity, and dependencies, exposing hidden maintenance and operational costs |

Add a task-specific persona only when the task gives it something distinct to find. Examples include the Security Paranoid, Privacy Zealot, Data Modeler, Algorithm Specialist, Accessibility Advocate, Test Saboteur, or a sharp domain expert. Use a Clean-slate Radical only when redesign is genuinely in scope. That candidate must identify compatibility breaks, migration work, data-loss risk, and irreversible choices.

The name supplies the worldview; the mandate ties it to observable work. For coding tasks, treat the persona as an execution bias: each candidate still inspects the repository, does the work in isolation, and runs the relevant checks.

Use one capable model across candidates unless the user or environment specifies otherwise. For coding candidates, prefer low reasoning effort; raise it only when measured complexity warrants it. For planning and architecture, prefer medium or high reasoning effort.

## Frame

Before spawning:

1. State the task contract every candidate receives, and what each one hands back.
2. Write one brief per candidate and explain the decision value of each.
3. Choose safe isolation. Candidates that write files need separate worktrees or directories; candidates must not edit the same files concurrently.
4. Record the concurrency and reasoning settings.
5. Note the disposition the user asked for, if any, so candidates emit whatever it needs — a rubric-friendly rationale, a machine-readable file, a diff, a timestamp.

The frame is complete when every candidate can receive the same task contract, one distinct brief, and one isolated output location.

## Fan out

Launch candidates up to `N`, limited by available system slots and resources. Each receives:

- the common task and grounding context;
- one approach and its persona lens;
- its isolated output path;
- instructions to do the work and add a short rationale naming alternatives considered and rejected.

Never exceed a user-supplied panel size or platform limits, and never sacrifice isolation to reach a target number.

If the user asked for a disposition that depends on ordering or timing — fastest wins, first to clear a bar — respect it while candidates run rather than waiting on the full set. Otherwise let them all finish.

If a candidate drops out, record it and report what remains. Replace it only when the user asked for a fixed panel size and another run is safe.

## Present the results

Report what ran and hand back what it produced. Keep the candidates distinct and attributed: do not silently merge, rank, or drop them unless that is what the user asked for.

Include:

- the personas, approaches, `N`, concurrency, and reasoning settings actually used;
- one line per candidate on what decision it could change;
- each candidate's output location and its rationale;
- dropouts, failures, and anything a candidate could not complete;
- whatever the requested disposition calls for.

Then do what the user asked for with the results, if anything: return them all, return one, score them, route them to another skill or tool, or stop here. When the user gave no instruction, present the set and let them choose.
