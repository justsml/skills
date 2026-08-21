# Platform notes for scorer implementation

- **Braintrust:** Implement one scorer per construct and return auditable metadata. Use library scorers as patterns, not prevalidated measurements. [Source](https://github.com/braintrustdata/eval-library)
- **DeepEval:** Use deterministic or custom metrics before G-Eval-style judges when rules suffice. Keep metric reasons concise and evidence-based. [Source](https://deepeval.com/docs/getting-started)
- **Inspect AI:** Implement scorers against the task's actual state and trajectory shape. Preserve per-sample evidence for later validation. [Source](https://inspect.aisi.org.uk/)
- **LangSmith:** Test evaluators locally on known good and bad examples before upload. Local and hosted return conventions can differ. [Source](https://github.com/langchain-ai/langsmith-skills/blob/main/config/skills/langsmith-evaluator/SKILL.md)
- **Langfuse:** Prefer repo-owned SDK evaluators for testable scorer code, or ingest external results as scores. Hosted code evaluators have no network or third-party packages, a two-second limit, and unstable management endpoints. Hosted observation evaluators see only the matched observation. Use stable score IDs and preserve name and timestamp too, since all three must match for overwrite semantics. [Code evaluators](https://langfuse.com/docs/evaluation/evaluation-methods/code-evaluators) [Scores via SDK](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk)
- **Phoenix:** Derive evaluator criteria from reviewed failure categories. Prefer deterministic evaluators and binary labels before broad Likert judges. [Source](https://github.com/Arize-ai/phoenix/blob/main/.agents/skills/phoenix-evals/SKILL.md)

Creating a hosted evaluator is an external mutation and may upload examples. Confirm scope first.
