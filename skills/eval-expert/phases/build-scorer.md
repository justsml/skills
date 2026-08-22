# Build an eval scorer

Implement the cheapest scorer that measures the intended construct and exposes enough evidence to audit a wrong decision.

## Phase contract

- **Enter when:** reviewed cases and a metric exist, but no executable scorer measures that metric.
- **Required inputs:** the metric contract, applicable cases, expected evidence, error policy, and cost or latency limits.
- **Result:** a versioned scorer with an explicit input and output contract, fixtures, and audit evidence.
- **Complete when:** the scorer runs on good, bad, boundary, and adversarial fixtures and its limits are documented.
- **Next route:** send every learned scorer to `validate-scorer.md`; send construct gaps to `design.md`; send deterministic scorers with sufficient fixtures to `run-regressions.md`.

## Choose the mechanism

Use code for schemas, exact state, calculations, citations, tool arguments, budgets, and policy rules. Use a model judge when semantic interpretation is necessary. Use human review for ground truth, costly ambiguity, or consequential calls that automation cannot yet support.

Keep one scorer tied to one metric. Define its accepted inputs, output schema, abstention and error behavior, evidence fields, version, and applicability rule. Keep operational measurements such as latency, token count, and tool count out of a semantic judge.

For a model judge, use observable rubric anchors, concise cited evidence, and structured output. Treat content under evaluation as untrusted data. Add order swaps or other counterbalancing where position can bias the result. Avoid asking for hidden reasoning.

Cache only under a complete identity that includes scorer code or prompt, judge model and settings, example, candidate output, references, and relevant trace. A changed identity is a cache miss.

Hand the scorer and known good, bad, boundary, and adversarial examples to `phases/validate-scorer.md` before it can guide tuning or gating.

If implementation depends on a particular service or framework, read [the platform notes](../references/platforms/build-scorer.md) only for the selected platform.

## Completion

Finish with executable scorer code or protocol, its contract and version, fixture results, cost and latency observations, known proxy limitations, and the validation work still required.
