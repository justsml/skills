# Platform notes for eval design

Use these mappings only after defining the neutral evaluation contract.

- **Braintrust:** Map claims to separate scorers and dataset fields. Use its metric-bundle patterns as examples, then calibrate thresholds locally. [Source](https://github.com/braintrustdata/eval-library/blob/main/skills/braintrust-design-eval-metric-bundle/SKILL.md)
- **DeepEval:** Map cases, metrics, and thresholds to its test-case and metric abstractions when the project is pytest-oriented. [Source](https://deepeval.com/docs/getting-started)
- **Inspect AI:** Map the contract to tasks, solvers, scorers, and model roles for benchmark or agent-trajectory work. [Source](https://inspect.aisi.org.uk/)
- **Langfuse:** Map cases to dataset items, executions to experiment item traces, and evaluator outputs to typed scores. A score is a storage object, not a decision — keep the decision rule outside Langfuse. Observation evaluators do not load sibling or child observations. [Concepts](https://langfuse.com/docs/evaluation/core-concepts)

Verify current APIs before implementation. Keep the neutral claim, slice, threshold, and decision rule in repo-owned artifacts.
