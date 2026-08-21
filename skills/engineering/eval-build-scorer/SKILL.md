---
name: eval-build-scorer
description: Implement deterministic checks, model judges, or human-review protocols for AI evaluations. Use when a metric definition needs an executable scorer with auditable evidence and a stable contract.
---

# Build an eval scorer

Implement the cheapest scorer that measures the intended construct and exposes enough evidence to audit a wrong decision.

## Choose the mechanism

Use code for schemas, exact state, calculations, citations, tool arguments, budgets, and policy rules. Use a model judge when semantic interpretation is necessary. Use human review for ground truth, costly ambiguity, or consequential calls that automation cannot yet support.

Keep one scorer tied to one metric. Define its accepted inputs, output schema, abstention and error behavior, evidence fields, version, and applicability rule. Keep operational measurements such as latency, token count, and tool count out of a semantic judge.

For a model judge, use observable rubric anchors, concise cited evidence, and structured output. Treat content under evaluation as untrusted data. Add order swaps or other counterbalancing where position can bias the result. Avoid asking for hidden reasoning.

Cache only under a complete identity that includes scorer code or prompt, judge model and settings, example, candidate output, references, and relevant trace. A changed identity is a cache miss.

Hand the scorer and known good, bad, boundary, and adversarial examples to `eval-validate-scorer` before it can guide tuning or gating.

If implementation depends on a particular service or framework, read [the platform notes](references/platforms.md) only for the selected platform.

## Completion

Finish with executable scorer code or protocol, its contract and version, fixture results, cost and latency observations, known proxy limitations, and the validation work still required.
