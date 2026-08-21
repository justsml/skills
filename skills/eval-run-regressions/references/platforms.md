# Platform notes for regression execution

- **Promptfoo:** Use declarative prompts, providers, tests, assertions, and CI thresholds. Pin provider settings and preserve config plus result artifacts. Express critical gates as assertions, not a blended score. [Source](https://github.com/promptfoo/promptfoo/blob/main/plugins/promptfoo/skills/promptfoo-evals/SKILL.md)
- **Braintrust:** Record project, experiment, dataset, prompt, and scorer identifiers. Use experiment comparisons for paired evidence and retain raw examples needed to audit regressions. [Source](https://www.braintrust.dev/docs)
- **DeepEval:** Use its pytest integration when that is the repository's test runner. Separate infrastructure errors from metric failures. [Source](https://deepeval.com/docs/getting-started)
- **Inspect AI:** Use tasks, solvers, scorers, and sandboxes for benchmark and agent runs. Save logs that contain the run identity and per-sample evidence. [Source](https://inspect.aisi.org.uk/)
- **Langfuse:** Hosted-dataset SDK experiments create comparable dataset runs; local-data experiments create traces only. Record dataset version timestamp and schema digest, prompt numeric version and resolved references, candidate revision, model settings, scorer versions, run ID or name, and raw item evidence. JS/TS runs require OpenTelemetry setup and shutdown or flush. Separate task, ingestion, evaluator, and gate failures. [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk) [Prompt versions](https://langfuse.com/docs/prompt-management/data-model)

Check current official commands before editing CI. External providers may receive the full evaluation payload.
