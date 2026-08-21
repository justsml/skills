# Platform notes for scorer implementation

- **Braintrust:** Implement one scorer per construct and return auditable metadata. Use library scorers as patterns, not prevalidated measurements. [Source](https://github.com/braintrustdata/eval-library)
- **DeepEval:** Use deterministic or custom metrics before G-Eval-style judges when rules suffice. Keep metric reasons concise and evidence-based. [Source](https://deepeval.com/docs/getting-started)
- **Inspect AI:** Implement scorers against the task's actual state and trajectory shape. Preserve per-sample evidence for later validation. [Source](https://inspect.aisi.org.uk/)
- **LangSmith:** Test evaluators locally on known good and bad examples before upload. Local and hosted return conventions can differ. [Source](https://github.com/langchain-ai/langsmith-skills/blob/main/config/skills/langsmith-evaluator/SKILL.md)
- **Phoenix:** Derive evaluator criteria from reviewed failure categories. Prefer deterministic evaluators and binary labels before broad Likert judges. [Source](https://github.com/Arize-ai/phoenix/blob/main/.agents/skills/phoenix-evals/SKILL.md)

Creating a hosted evaluator is an external mutation and may upload examples. Confirm scope first.
