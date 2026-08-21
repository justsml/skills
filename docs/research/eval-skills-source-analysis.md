# Source analysis: upstream evaluation skills

Research date: 2026-08-21

## Question and method

This note compares the evaluation skills named in the request. It separates reusable evaluation practice from platform mechanics and records what each source contributes, where it overlaps with the others, and where its advice needs qualification.

I read each linked `SKILL.md` from its owning repository. I also read the directly referenced files needed to understand judge design, validation, metric bundles, optimizer behavior, and trace coding. The source links below point to those first-party repository files.

One link has changed shape upstream. Promptfoo's linked `references/cheatsheet.md` no longer exists under the plugin path. The current sibling file is [`references/eval-patterns.md`](https://github.com/promptfoo/promptfoo/blob/main/plugins/promptfoo/skills/promptfoo-evals/references/eval-patterns.md). The community Phoenix skill is a copy of the much larger first-party Phoenix eval skill, so both are discussed separately.

## Findings by source

### LLM Judge

Sources: [`SKILL.md`](https://github.com/wenxuec/llm-judge/blob/main/SKILL.md), [repository README](https://github.com/wenxuec/llm-judge/blob/main/README.md)

Distinctive workflow:

1. Scope the system, desired qualities, available ground truth, and deployment risk before building anything.
2. Write an operational rubric with a scoring type and failure modes for every criterion.
3. Create one structured judge prompt per criterion, with explicit anchors and bias controls.
4. Generate a small Python runner, then add step attribution and content-addressed caching.
5. Calibrate against 20 to 50 human-labeled examples with Cohen's kappa for categorical labels or Spearman correlation for ordinal scores.

Reusable ideas:

- Keep criteria separate. Each criterion gets its own definition, scale, prompt, and result.
- Choose binary scores for hard constraints, a three-point scale for partial completion, and use five-point scales sparingly.
- Distinguish step-level failures from whole-trajectory outcomes.
- Track latency, tokens, tool count, and state changes with code rather than an LLM judge.
- Cache on the content of the example and rubric, including the judge model and prompt text. This makes incremental reevaluation safe after either data or rubric changes.
- Separate soft blame attribution from counterfactual causal attribution. The latter requires replay from an intermediate state and costs much more.

Vendor mechanics:

- The generated runner uses Anthropic or OpenAI SDK calls and environment variables.
- The skill says its templates can later be moved to DeepEval or Inspect AI.

Weak spots:

- It prescribes rationale before score as hidden chain-of-thought. A neutral skill should ask for concise evidence or a decision record, not private reasoning. Structured evidence is auditable without requiring hidden reasoning disclosure.
- Fixed agreement cutoffs are useful defaults but are not enough for release gating. The source does not make false acceptance severity, subgroup failures, uncertainty, or scorer-error propagation first-class.
- Soft blame weights are labeled correctly as non-causal, but users may still overread them. They should never appear under a causal name.
- It jumps from rubric design to harness generation before a dedicated failure-discovery phase.

Overlap:

- Rubric construction overlaps with Braintrust's metric-bundle skill.
- Judge calibration overlaps with Braintrust's scorer-validation skill.
- Incremental execution overlaps with Promptfoo.
- Trajectory handling overlaps with LangSmith and Phoenix.

### EvalSurfer

Sources: [`SKILL.md`](https://github.com/di37/EvalSurfer/blob/main/skills/eval-surfer/SKILL.md), [repository README](https://github.com/di37/EvalSurfer/blob/main/README.md), [governance mapping](https://github.com/di37/EvalSurfer/blob/main/docs/governance-mapping.md)

Distinctive workflow:

- CIMAA divides work into Core, Interface, Metrics, Analysis, and Assurance.
- A deterministic planner infers which criteria apply to the available sample and records why it skipped the rest.
- The agent judges qualitative and safety criteria. Tools compute operational, reference, coverage, calibration, and regression metrics.
- Reports include assessed coverage and a decision, then pass through schema validation and gates.

Reusable ideas:

- Applicability is data-dependent. Record `not assessed` with a reason instead of inventing evidence.
- Coverage means assessed divided by applicable, not assessed divided by every criterion in a universal catalog.
- Keep agent judgment and deterministic measurement separate.
- Treat quality, operations, and safety as different report sections, even when a final release decision combines constraints from each.
- Include cross-harness invariance, dataset contamination, dataset diffs, red-team cases, and policy gates in a mature evaluation system.
- Governance mappings should point to evidence fields. They do not certify compliance.

Vendor mechanics:

- EvalSurfer exposes Python, CLI, and MCP interfaces with a common set of deterministic helpers.
- It includes adapters for Promptfoo, OpenTelemetry, LangSmith, Langfuse, and Ragas.

Weak spots:

- Default 1-to-5 scores and global pass thresholds make the workflow easy to start, but they conflict with stronger advice elsewhere to prefer binary decisions and locally calibrated thresholds.
- The large criterion and tool catalog risks turning one skill into a platform manual.
- Safety is assessed by default, but the generic scorecard does not itself establish that the safety evaluator is valid enough to gate.
- The overall score can invite tradeoffs between constructs that should remain separate constraints.

Overlap:

- The deterministic-first principle appears in agent-eval and Phoenix.
- Its planner and coverage record are valuable additions missing from the five-skill shortlist.
- Its tool catalog spans discovery, design, execution, validation, and gating, which are better separated in a neutral skill set.

### agent-eval

Sources: [`SKILL.md`](https://github.com/ericrisco/rsc-harness/blob/main/skills/agent-eval/SKILL.md), [`judge-design.md`](https://github.com/ericrisco/rsc-harness/blob/main/skills/agent-eval/references/judge-design.md), [`runner-and-gate.md`](https://github.com/ericrisco/rsc-harness/blob/main/skills/agent-eval/references/runner-and-gate.md)

Distinctive workflow:

- It reduces every framework to five stages: dataset, runner, scorers, metrics, and gate.
- It starts with a versioned, real-world golden set organized by failure mode.
- Its default scorer mix is roughly 60 percent deterministic, 30 percent judge, and 10 percent human.
- It recommends pairwise, position-swapped judging, human calibration, bootstrap confidence intervals, and regression gates against a committed baseline.
- It offers side-by-side implementation guidance for DeepEval and Inspect AI.

Reusable ideas:

- The dataset is the durable asset. Frameworks and runners are replaceable.
- Tag every case by failure mode so aggregates can be sliced into actionable regressions.
- Use the cheapest scorer that measures the construct. Do not spend judge calls on schema, exact-match, or budget checks.
- Gate regressions against a baseline with uncertainty rather than using a noisy absolute threshold alone.
- Score both the agent's path and final outcome.
- Keep offline evaluation, production observability, red teaming, and product A/B tests as related but separate disciplines.

Vendor mechanics:

- DeepEval fits Python and pytest-oriented CI.
- Inspect AI has a task, solver, scorer model and stronger trajectory and safety support.
- The references show both mappings while retaining a provider-neutral scorer protocol.

Weak spots:

- Numeric prescriptions such as 50 to 200 cases per failure mode and the 60/30/10 mix are heuristics, not evidence-backed invariants. They should appear as starting points with cost and risk caveats.
- "Judge model at least as strong as the system" is too coarse. Judge validity is criterion-specific and empirical.
- A regression-only gate can preserve a bad baseline. A mature gate needs both non-regression checks and fixed safety or product tolerances.
- Some time-sensitive framework/version claims in the cheat sheet need re-verification before reuse.

Overlap:

- Its neutral anatomy is the best conceptual base for Promptfoo, Braintrust, LangSmith, Phoenix, DeepEval, or Inspect adapters.
- Calibration guidance is less complete than Braintrust's scorer-validation protocol.
- Failure discovery is asserted as dataset construction but is not worked as systematically as Phoenix open and axial coding.

### deepeval-bcg

Sources: [`SKILL.md`](https://github.com/EvXata/deepeval-bcg/blob/main/.agents/skills/deepeval/SKILL.md), [`4-tier-architecture.md`](https://github.com/EvXata/deepeval-bcg/blob/main/.agents/skills/deepeval/references/4-tier-architecture.md), [`bcg-rubric.md`](https://github.com/EvXata/deepeval-bcg/blob/main/.agents/skills/deepeval/references/bcg-rubric.md), [`novelty-checklist.md`](https://github.com/EvXata/deepeval-bcg/blob/main/.agents/skills/deepeval/references/novelty-checklist.md), [`skeptic-agent.md`](https://github.com/EvXata/deepeval-bcg/blob/main/.agents/skills/deepeval/references/skeptic-agent.md), [`tier2-judge-prompt.md`](https://github.com/EvXata/deepeval-bcg/blob/main/.agents/skills/deepeval/references/tier2-judge-prompt.md), [`cadence-day-week-30day.md`](https://github.com/EvXata/deepeval-bcg/blob/main/.agents/skills/deepeval/references/cadence-day-week-30day.md)

Distinctive workflow:

- Four cost tiers move from structural checks to heuristics, a runtime-agent judge, and sampled human review.
- The rubric targets strategic-analysis artifacts rather than general LLM applications. It scores structure, ambiguity handling, prioritization, rigor, non-obviousness, synthesis, independence, and actionability.
- Critical dimensions can force revision even when the weighted average passes.
- A skeptic applies ambiguity, sycophancy, and steelman-the-opposite attacks.
- A ten-signal novelty test combines baselines, surprise, insider evidence, counter-narratives, falsifiability, expert review, and short-horizon behavior.

Reusable ideas:

- Escalate evaluation by cost and risk rather than applying an expensive judge to every artifact.
- Make ambiguity handling and resistance to a flawed user premise explicit criteria.
- A critical-criterion veto is safer than allowing an average to wash out a severe failure.
- Test a claimed insight against a baseline and an opposite case. Novelty should be falsifiable, not just unusual wording.
- Attach an owner, near-term action, and leading indicator to advice that claims to be actionable.

Vendor mechanics:

- Codex itself performs tier-two judgment in the active session and writes a verdict file.
- Local Python scripts prepare prompts and aggregate the result.
- The feedback step can post a GitHub issue to the upstream repository.

Weak spots:

- "BCG-calibrated" and "MBB-grade" are branding claims unless the repository provides an external validation study. The rubric may be useful, but those labels should not be inherited by a neutral skill.
- Runtime self-judgment is not reproducible across agent versions, context, or hidden system instructions unless the run records those conditions.
- Posting feedback externally is an unrelated side effect and should require explicit authorization.
- Its weighted novelty formula mixes manual, automatic, human, and behavioral signals without a demonstrated calibration basis.
- A hard 30-day cap is specific to its consulting use case, not a general evaluation principle.

Overlap:

- Tiering supports the deterministic, judge, human split in agent-eval.
- The skeptic and novelty probes are valuable specialty references, not a general core workflow.
- Critical vetoes belong in metric-bundle and release-gate design.

### Community phoenix-evals

Sources: [`SKILL.md`](https://github.com/stanfish06/skillquarium/blob/master/skills/phoenix-evals/SKILL.md), [first-party Phoenix eval skill](https://github.com/Arize-ai/phoenix/blob/main/.agents/skills/phoenix-evals/SKILL.md)

Distinctive workflow:

- Start with tracing, error analysis, and axial coding before selecting evaluators.
- Prefer custom checks derived from observed failures, deterministic code before an LLM judge, and binary labels before Likert scales.
- Validate evaluators against humans and target greater than 80 percent true-positive and true-negative rates.
- Gate hard invariants per case. Treat judge scores as aggregate quality signals.

Reusable ideas:

- "Error analysis first" is the strongest contribution. Evaluation criteria should come from observed failures, not a generic catalog.
- Separate invariants from trend signals. A flaky semantic judgment should not fail one case in CI the same way a schema violation does.
- Check both sensitivity and specificity. Aggregate agreement can hide a judge that accepts every output.

Vendor mechanics:

- The reference tree maps the lifecycle to Phoenix evaluators, datasets, experiments, tracing, pytest, Vitest, Jest, production sampling, and guardrails.
- Python and TypeScript paths are first-class.

Weak spots:

- The community copy is a thin router into dozens of first-party Phoenix references. Without those files it is incomplete.
- A fixed 80 percent TPR/TNR target ignores prevalence, severity, uncertainty, and the cost of false acceptance.
- The short skill does not specify sample design or how to prevent tuning and validation leakage.

Overlap:

- Its judge validation belongs with Braintrust's more complete validation protocol.
- Its regression execution overlaps with Promptfoo.
- Its failure discovery is expanded by Phoenix CLI open and axial coding.

### GEPA optimize-anything

Sources: [`SKILL.md`](https://github.com/gepa-ai/gepa/blob/main/.claude/skills/gepa-optimize-anything/SKILL.md), [`api.md`](https://github.com/gepa-ai/gepa/blob/main/.claude/skills/gepa-optimize-anything/references/api.md), [`gotchas.md`](https://github.com/gepa-ai/gepa/blob/main/.claude/skills/gepa-optimize-anything/references/gotchas.md), [`tracking.md`](https://github.com/gepa-ai/gepa/blob/main/.claude/skills/gepa-optimize-anything/references/tracking.md), [`writing_evaluators.md`](https://github.com/gepa-ai/gepa/blob/main/.claude/skills/gepa-optimize-anything/references/writing_evaluators.md)

Distinctive workflow:

- The candidate is any text artifact. The evaluator returns a scalar score plus feedback.
- The same evaluator can drive GEPA reflective evolutionary search, agentic search backends, or a best-of-N baseline.
- Modes distinguish one hard problem, a shared candidate over several tasks, and held-out generalization.
- A sealed test set reports the seed and final scores after search. It never enters search or selection.
- Budgets are sized in evaluator calls, with explicit score, token-cost, and wall-clock stop conditions.

Reusable ideas:

- Treat optimization as a client of the evaluation system. It does not design or validate the metric.
- Give the optimizer structured, actionable feedback, not only a scalar.
- Split optimization, selection, and final reporting data. Repeated selection on the same validation set creates optimistic bias.
- Average repeated samples inside the evaluator for stochastic systems.
- Compare the optimizer with a naive search baseline.
- Preserve a full candidate and evaluation history, including seed, configuration, and budget.

Vendor mechanics:

- `optimize_anything` and its `OptimizeAnythingConfig` select GEPA, AutoResearch, MetaHarness, or best-of-N.
- GEPA accepts LiteLLM identifiers or a compatible callable. Agentic backends shell out to Claude Code and can use Bubblewrap on Linux.
- Weights & Biases and MLflow can record runs.

Weak spots:

- The optimizer will exploit any metric defect. The skill warns about this, but a neutral workflow should make validated evaluator fitness a precondition for optimization.
- Multi-objective information can appear in feedback, but the optimizer contract remains one scalar. Collapsing safety, quality, and cost into that scalar creates Goodhart risk.
- The stated budget multiplier is a backend-specific heuristic.
- Evaluation caching can let repeated candidates continue without consuming the nominal evaluation budget, so stop conditions need careful design.

Overlap:

- GEPA should consume outputs from metric design, scorer validation, and regression-suite skills. It should not absorb those jobs.
- Its test-set discipline is stronger than most other sources in this list.

### Braintrust validate-eval-scorer

Sources: [`SKILL.md`](https://github.com/braintrustdata/eval-library/blob/main/skills/braintrust-validate-eval-scorer/SKILL.md), [`validation-recipe.md`](https://github.com/braintrustdata/eval-library/blob/main/skills/braintrust-validate-eval-scorer/references/validation-recipe.md), [`interaction-contract.md`](https://github.com/braintrustdata/eval-library/blob/main/skills/braintrust-validate-eval-scorer/references/interaction-contract.md), [`platform-mechanics.md`](https://github.com/braintrustdata/eval-library/blob/main/skills/braintrust-validate-eval-scorer/references/platform-mechanics.md)

Distinctive workflow:

- Name the reference tier first. Adjudicated human labels support a fitness verdict; strong-model labels only support iteration.
- Align candidate and reference at both item and criterion level.
- Report kappa or alpha with uncertainty, then inspect confusion by class and severity.
- Lead with dangerous false acceptances, test known regressions and improvements, probe shortcuts, and slice by subgroup.
- Propagate scorer error into any headline result and issue an explicit fitness verdict with allowed uses, prohibited uses, and revalidation triggers.

Reusable ideas:

- Validate a scorer as a measuring instrument. High overall accuracy is not sufficient.
- Keep scorer development data separate from scorer validation data.
- Validate directional sensitivity with injected degradations and improvements.
- Probe length, confidence, polish, judge-directed text, and subgroup effects as possible shortcuts.
- Validity expires when the scorer, rubric, judge model, data distribution, or use changes.
- A scorer can be fit for exploration or monitoring but unfit for release gating.

Vendor mechanics:

- Braintrust stores the reference set as a versioned dataset and the validation run as an experiment.
- Scorer evidence goes in span output. Scorer name and version go in metadata.
- Custom columns or an exported notebook compute agreement and confusion matrices. Disagreements return to a review queue.

Weak spots:

- The skill assumes a reference set and scorer already exist, so a neutral suite needs explicit handoffs from dataset and scorer-design work.
- Braintrust platform instructions are mixed into the core skill, although the method is almost entirely portable.
- Fitness bands referenced by the recipe are defaults, not universal release criteria.

Overlap:

- This is the strongest source for scorer calibration and should own that concern in the synthesized set.
- It subsumes the lighter calibration advice in LLM Judge, agent-eval, and Phoenix.

### Braintrust design-eval-metric-bundle

Sources: [`SKILL.md`](https://github.com/braintrustdata/eval-library/blob/main/skills/braintrust-design-eval-metric-bundle/SKILL.md), [`metric-bundle.md`](https://github.com/braintrustdata/eval-library/blob/main/skills/braintrust-design-eval-metric-bundle/references/metric-bundle.md), [`interaction-contract.md`](https://github.com/braintrustdata/eval-library/blob/main/skills/braintrust-design-eval-metric-bundle/references/interaction-contract.md), [`platform-mechanics.md`](https://github.com/braintrustdata/eval-library/blob/main/skills/braintrust-design-eval-metric-bundle/references/platform-mechanics.md)

Distinctive workflow:

- Keep quality, safety, reliability, latency, and cost as separate measures.
- Give each metric one decision role: improve or guardrail.
- Record direction, threshold type, proxy limitation, and gaming path.
- Scope the primary metric to the causal path the change can affect. Keep an aggregate nearby to detect collateral damage.
- Measure cost per resolved request, including retries, fallbacks, and human cleanup.

Reusable ideas:

- Never average guardrails into an optimization score. A safety regression must not be offset by lower latency.
- Use an upper confidence bound for rare harmful-event rates.
- Fix thresholds from product tolerance before running the experiment.
- Require more than one proxy for outcomes important enough to gate.
- Pair a narrow, intervention-sensitive metric with a broad blast-radius check.
- Name how each metric can be gamed before optimizing it.

Vendor mechanics:

- Braintrust maps one metric to one scorer and one visible score column.
- Tokens, latency, and cost use native metrics. Derived measures use custom columns.
- Guardrails become experiment-level regression gates, and the same scorers can run online.

Weak spots:

- It deliberately does not design scorers, datasets, or instrumentation. Those handoffs must be explicit in a neutral suite.
- "All five dimensions" is a good checklist, but some tasks should waive irrelevant dimensions with a written reason rather than manufacture a metric.

Overlap:

- This source provides the cleanest answer to metric architecture.
- Its guardrail distinction corrects weighted scorecards used by several other skills.

### Promptfoo evals

Sources: [`SKILL.md`](https://github.com/promptfoo/promptfoo/blob/main/plugins/promptfoo/skills/promptfoo-evals/SKILL.md), [`eval-patterns.md`](https://github.com/promptfoo/promptfoo/blob/main/plugins/promptfoo/skills/promptfoo-evals/references/eval-patterns.md)

Distinctive workflow:

- State one product question and begin with 3 to 10 success and known-failure cases.
- Prefer deterministic assertions, then use model-graded rubrics only for semantic properties.
- Keep prompts and growing test sets in files, validate the config, run without cache or sharing during development, and inspect the exported JSON.
- Add cases and tighten assertions in response to actual false passes and failures.

Reusable ideas:

- A regression suite should answer a named product question, not become an unbounded assertion catalog.
- Make fresh execution explicit while developing.
- Export a machine-readable artifact and inspect the raw output, score, reason, and error rather than trusting a summary count.
- Keep provider setup, non-adversarial eval authoring, and red teaming separate.
- Use a single parsing transform when several assertions inspect structured output.

Vendor mechanics:

- YAML configs define prompts, providers, tests, assertions, transforms, and CI behavior.
- Assertion types include exact, substring, regex, JSON, JavaScript, and `llm-rubric`.
- `promptfoo validate` and `promptfoo eval` create executable local and CI suites.

Weak spots:

- A 3-to-10-case starter is appropriate for smoke testing, not for estimating release risk.
- The skill focuses on suite execution. It does not establish dataset representativeness, judge validity, or uncertainty.
- `npx ...@latest` weakens reproducibility. A committed suite should pin a tested CLI version in its project or CI environment.
- `--no-cache` is right during authoring but is not a general ban on content-addressed evaluation caches.

Overlap:

- Promptfoo is an execution adapter, not the neutral method.
- Its deterministic-first assertion strategy fits agent-eval and Phoenix.

### LangSmith evaluator

Source: [`SKILL.md`](https://github.com/langchain-ai/langsmith-skills/blob/main/config/skills/langsmith-evaluator/SKILL.md)

Distinctive workflow:

- Inspect a real dataset example, run output, and trace before writing extraction or evaluation code.
- Separate offline evaluators attached to datasets from online evaluators attached to projects.
- Create one evaluator per metric.
- Test run functions and evaluators locally, then upload deterministic or LLM evaluators with explicit targets.
- Uploaded dataset evaluators run automatically on experiments. Online evaluators inspect production runs without a dataset reference.

Reusable ideas:

- Never assume the output or trajectory schema. Inspect it first.
- Shape the run function output to match the dataset schema when possible.
- Keep one evaluator tied to one metric so failures remain visible.
- Test on known good and bad examples before attaching an evaluator to automated runs.
- Distinguish local evaluation, offline experiments, and online scoring.

Vendor mechanics:

- The `langsmith` CLI creates, lists, uploads, replaces, and deletes evaluators.
- Structured LLM judges require a server-supported model configuration and an explicit dataset or project.
- Uploaded code evaluators run in a restricted sandbox and should use only available packages.
- LangGraph trajectory capture can use debug streaming with subgraphs. Custom agents must expose or reconstruct their own trajectory.

Weak spots:

- The skill is mostly operational documentation. It does not say how to discover failures, design metric bundles, or validate a judge statistically.
- CLI OAuth and SDK API-key authentication can point at different workspaces. This is a platform trap, not an evaluation principle.
- Name-based deletion can affect every rule with the same display name. A neutral adapter should flag destructive and ambiguous operations and require confirmation.
- Uploaded and local evaluator return conventions differ, which increases migration risk.

Overlap:

- The trace inspection rule belongs in a neutral failure-discovery skill.
- LangSmith is a viable adapter for both offline execution and production evidence, but it should not define the core artifact schema.

### Phoenix CLI

Sources: [`SKILL.md`](https://github.com/Arize-ai/phoenix/blob/main/.agents/skills/phoenix-cli/SKILL.md), [`open-coding.md`](https://github.com/Arize-ai/phoenix/blob/main/.agents/skills/phoenix-cli/references/open-coding.md), [`axial-coding.md`](https://github.com/Arize-ai/phoenix/blob/main/.agents/skills/phoenix-cli/references/axial-coding.md)

Distinctive workflow:

- Choose the unit of analysis first: trace for a stateless run, session for multi-turn behavior, or span for a local mechanical failure.
- Sample records and perform open coding with concrete notes before inventing a taxonomy.
- Use a shared coding-run identifier and a local JSONL sidecar so the review is queryable and reversible.
- Consolidate observations through axial coding into categories that can drive datasets and evaluators.
- Inspect datasets and experiments after the failure model exists.

Reusable ideas:

- Production traces are evidence for failure discovery, not a ready-made eval set.
- Pick the unit at which the failure actually occurs before sampling or labeling.
- Keep raw observations separate from the later taxonomy. This reduces premature category forcing.
- Give every coding pass a provenance identifier and retain a deterministic local handoff.
- Make annotation writes reversible by identifier.
- Turn recurrent categories into candidate evaluator criteria and representative cases.

Vendor mechanics:

- `px` lists and fetches traces, spans, sessions, datasets, experiments, and annotation configurations.
- Phoenix supports categorical, continuous, and free-form annotations, plus GraphQL filters over trace-, span-, and session-grain fields.
- The CLI can attach notes and labels to server records and maintain `.px/coding/*.jsonl` sidecars.
- Setup can register tracing and verify that a trace arrived.

Weak spots:

- The 600-line skill is a CLI manual plus a research workflow. A neutral skill should retain open and axial coding while moving commands to an adapter.
- Annotation mutation and deletion require explicit authorization and careful identifiers.
- Sampling strategy, representativeness, and privacy controls need more attention before mining production data.
- Coding produces hypotheses and a taxonomy. It does not validate that the resulting evaluator measures them reliably.

Overlap:

- Phoenix supplies the strongest failure-discovery stage in the shortlist.
- LangSmith can supply similar trace evidence, but its evaluator skill does not describe open and axial coding.
- The coding output should feed metric design, dataset curation, and scorer construction.

## Cross-source synthesis

### The reusable lifecycle

The sources support a seven-part lifecycle:

1. Discover failures from production traces, user reports, incident records, and known edge cases. Preserve raw observations before taxonomy work.
2. Define the evaluation objective, scope, unit of analysis, applicable criteria, and evidence coverage.
3. Design a metric bundle with separate improvement metrics and non-regression guardrails.
4. Build versioned cases from real failures, add deliberate counterexamples, and reserve separate tuning, validation, and test splits.
5. Implement the cheapest valid scorer for each metric. Use code for deterministic properties and judges for semantic ones.
6. Validate every scorer against independent reference labels, then assign allowed and prohibited uses.
7. Execute regression suites and production monitoring. Only after the evaluator is valid should an optimizer search against it.

The order matters. GEPA is powerful only after metric and scorer validity. Promptfoo executes a suite but does not make it representative. LangSmith and Phoenix expose production evidence but do not turn that evidence into a valid gate on their own.

### Artifacts that should stay platform-neutral

A neutral skill set should define these artifacts without Braintrust, Promptfoo, LangSmith, Phoenix, DeepEval, or Inspect types:

- `eval-objective.md`: decision, users, risks, deployment context, unit of analysis.
- `failure-taxonomy.yaml`: category definitions, examples, provenance, severity, unresolved observations.
- `metric-bundle.yaml`: metric, construct, role, direction, threshold, uncertainty rule, proxy limitation, gaming path, applicable slice.
- `cases.jsonl`: stable ID, input, expected evidence or behavior, context, failure-mode tags, provenance, split, sensitivity.
- `scorers/`: one scorer contract per metric with version, evidence output, and deterministic or judge implementation.
- `scorer-validation.json`: reference tier, sample version, agreement with interval, confusion by severity, subgroup slices, shortcut probes, allowed uses, prohibited uses, expiry triggers.
- `experiment-manifest.yaml`: system version, dataset version, scorer versions, provider and model configuration, seeds, sample count, cache policy, cost budget.
- `eval-results.json`: per-case raw outputs and evidence, separate metric columns, operational measurements, errors, and provenance.
- `gate-policy.yaml`: absolute safety and product floors, regression rules, uncertainty handling, and escalation to human review.

### What should not be consolidated

One giant evaluation skill would repeat EvalSurfer's main weakness. It would mix research judgment, statistical validation, provider setup, CLI commands, and mutation permissions in a file too large to apply reliably.

The best neutral set has focused skills with explicit handoffs:

- `discover-eval-failures`
- `design-eval-objective-and-metrics`
- `build-eval-dataset`
- `build-eval-scorers`
- `validate-eval-scorers`
- `run-eval-regressions`
- `optimize-against-evals`

`plan-agent-eval` can route across these when the user needs an end-to-end plan. Trace discovery should remain separate because it has different permissions and privacy risk. Optimization should remain separate because it magnifies metric defects.

### Where platform hints belong

Put provider instructions in sibling references, grouped by concern, not in one universal platform skill. A single `platforms.md` will grow into a long routing table and force every skill invocation to load irrelevant commands.

A practical layout is:

```text
skills/engineering/<skill>/
  SKILL.md
  references/
    artifact-contract.md
    adapters/
      braintrust.md
      deepeval.md
      inspect-ai.md
      langsmith.md
      phoenix.md
      promptfoo.md
      gepa.md
```

Only add an adapter where that platform supports the skill's concern. For example, `discover-eval-failures` needs LangSmith and Phoenix hints, while `optimize-against-evals` needs GEPA hints. Shared setup, authentication, privacy, and external-upload warnings can live once under `skills/engineering/eval-platform-adapters/references/`, but the task skill should link directly to the relevant section.

Each adapter should map the neutral artifact to the provider's object model and include:

- current official command or SDK shape;
- auth and data-upload behavior;
- local versus hosted execution differences;
- destructive or ambiguous operations;
- import and export mapping;
- unsupported neutral fields or semantic loss;
- a verification command.

### Corrections to carry into the new skills

- Ask for concise evidence, not hidden chain-of-thought.
- Treat fixed sample sizes, scorer mixes, pass scores, and agreement cutoffs as starting points. Calibrate them to prevalence, severity, and decision cost.
- Use both absolute guardrails and regression checks. Either one alone is incomplete.
- Keep safety, quality, reliability, latency, and cost separate. Do not trade them through a weighted average.
- Validate the scorer before optimization or release gating.
- Record model, provider, prompt, scorer, dataset, and harness versions so results can be reproduced.
- Require explicit approval before uploading private traces or datasets, creating hosted evaluators, annotating shared records, or deleting remote objects.
- Treat synthetic data as coverage support, never the only source of a release set.
- Make production trace sampling privacy-aware and document selection bias.

## Bottom line

The proposed shortlist has the right core pieces but needs two changes. First, Phoenix-style open and axial coding should be a first-class failure-discovery skill, not merely a platform choice at the end. Second, dataset construction and scorer implementation need their own neutral handoff between metric design and scorer validation.

Braintrust contributes the strongest metric and validity contracts. GEPA contributes the optimization loop and disciplined test-set separation. Promptfoo contributes executable regressions. Phoenix contributes evidence-driven failure discovery. LangSmith contributes careful run-shape inspection and offline versus online deployment mechanics. The neutral skill set should own the artifacts and lifecycle. Provider references should only explain how to realize those artifacts on a given platform.
