# Platform notes for eval optimization

- **GEPA:** Represent editable system parts as named text components. Supply a metric that returns a score and concise feedback. Keep the held-out set outside the search loop, checkpoint candidates, and preserve lineage. GEPA proposes and searches; validated scorers still own the objective. [Source](https://github.com/gepa-ai/gepa/blob/main/.claude/skills/gepa-optimize-anything/SKILL.md)
- **Braintrust:** Use experiment history and scorer evidence to compare proposed candidates, but keep optimizer feedback data separate from final validation data. [Source](https://www.braintrust.dev/docs)
- **Promptfoo:** Use a fixed regression config to compare exported candidates when the optimization engine itself is elsewhere. [Source](https://github.com/promptfoo/promptfoo/blob/main/plugins/promptfoo/skills/promptfoo-evals/SKILL.md)
- **Langfuse:** Use experiment history and trace-linked prompt versions as evidence, but run the search outside Langfuse. Fetch prompts by numeric version, never a mutable label, and record the compiled content and config for every candidate. Creating a prompt version or moving `production` is an external mutation. [Prompt concepts](https://langfuse.com/docs/prompt-management/data-model)

Pin model and provider settings, set an explicit run budget, and verify current APIs before starting a paid search.
