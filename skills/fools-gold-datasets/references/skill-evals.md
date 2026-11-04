# Evaluate the generator skill, not just its helpers

A strong skill should improve actual artifacts without excessive retries. Test activation, execution, final state and efficiency separately. A model saying “I used native tables” is not evidence of table structure.

## Three evidence layers

1. **Offline regression checks:** schema validation, helper tests, invalid receipts, Unicode leaks, metadata sanitization and rubric arithmetic. Fast and deterministic; they establish only their tested behavior.
2. **Agent task trials:** run realistic requests in isolated workspaces with the actual skill, controlled tools and recorded traces. Inspect resulting native files, renders, references and retained failures.
3. **Transfer confirmation:** use new domains, layouts, producers and tasks not used to edit the skill; assess label reliability and downstream usefulness independently.

The repository’s `eval/cases/fools-gold-datasets.json` tests routing/contracts. Its hand-written baseline observations are not model results. The [behavioral assets](../evals/) supply separate tasks and grading support; use their documented runner contract. Helper tests passing does not establish that agents follow the skill.

## Start with a small meaningful suite

Include at least these distinct tasks before expanding:

- Original technical report with a real table, meaningful quantities/units and typeset equations; verify native structure and rendered-label agreement.
- Restricted-source replacement with a metadata-only canary; verify the Builder sees only the sanitized handoff.
- Mixed native/raster corpus with independent factors and protected lineage; verify actual transforms and complete inventory.

Add failure-derived cases: infeasible cell/header widths, formatting-compatible math, wrong-sign/swap mutations, screenshot commentary, reordered page reuse, cloned bytes versus page subsets, hidden text, stale evidence, unavailable native-equation support and checker false positives. Include ordinary summary/edit requests that should not activate the skill. Keep acceptance criteria visible in the user contract; keep reference answers, canaries and grading implementation outside the agent workspace.

## Run paired baseline and candidate trials

Freeze task inputs, skill revision, grader revision, environment/tool/font versions and permissions. Compare **no skill**, previous skill and revised skill on the same feasible tasks where budget allows. Use fresh isolated contexts and deterministic seeds for generators; record model nondeterminism rather than assuming temperature makes runs identical.

Run several independent trials per task/model/host. Report first-attempt success and all-trials consistency; best-of-many success alone rewards expensive thrashing. Keep failed attempts and refusals in the denominator. Present per-task/slice results and paired differences with uncertainty at the independent task/family level. A few smoke trials are behavior evidence, not a statistically established improvement.

Capture the actual native trace and artifacts. For Codex, `codex exec --json` is one supported trace route; verify current CLI options and the skill-load event. For Claude, use the installed host’s documented skill/plugin evaluation workflow when available; verify packaging and flags rather than assuming a loose skill is a plugin. Record exact model/options and budget. No live run inherits permission to use arbitrary credentials or access production/source data.

## Grade outcomes and process independently

| Dimension | Evidence |
| --- | --- |
| Meaning | Independent calculations, units/assumptions, coherent claims, localized expert rubric |
| Native fidelity | Real cells/spans/equation representation, saved artifact reopened and exported |
| Presentation | Full-page readability plus dense/hard-region inspection; blind pairwise preference with reasons |
| Labels | Exact field/region comparison, ownership/order, uncertainty and reviewed coverage |
| Integrity | Source access trace, split ancestry, complete inventory, immutable inputs and evidence bindings |
| Efficiency | Wall time to first useful preview and accepted artifact, build rounds, retries, token/cost use |

Use critical pass/fail gates plus a small quality rubric. Calibrate model judges against blinded expert/human judgments before release use; randomize pair order and inspect disagreement, verbosity and position biases. Judge the artifact without the Builder’s persuasive summary. Predeclare disclosure placement, native editability and representation requirements; a reviewer’s preference for an on-page synthetic notice or a particular producer must not become a hidden pass criterion. Preserve both the raw preference and any rubric adjudication. Do not require one exact tool sequence when multiple implementations satisfy the task.

Mutation-test graders: a correct artifact must pass; a one-cell value swap, missing unit, substituted formula, omitted section, misplaced quotation, malformed receipt or wrong source binding must fail the relevant dimension. Unsupported checks abstain explicitly. Review unexpected “failures” for grader or task bugs before changing the skill.

## Iterate and release honestly

Use development failures to add the smallest useful instruction. Keep successful cases as regressions; retain harder capability tasks separately. Reserve new tasks for confirmation and do not repeatedly inspect them while tuning. Report checks executed, model/task coverage, results, limitations and actual costs. A stronger written workflow is a hypothesis until paired trials support it.

## Official guidance used

Checked 2026-10-27; recheck host-specific features before running:

- [OpenAI: Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills): observable outcomes/process/style/efficiency, captured traces and artifact checks.
- [OpenAI: Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices): task-specific evals, representative cases, calibrated human/model judgment and continuous evaluation.
- [Anthropic: Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices): evaluation-first iteration, concise progressive disclosure and verifiable intermediate outputs.
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/research/demystifying-evals-for-ai-agents): grade outcomes as well as traces, separate capability from regression tests, and distinguish occasional success from reliable repeated success.

These sources inform the method; none certifies this skill or the generated corpus.
