# Platform notes for eval optimization

- **GEPA:** Represent editable system parts as named text components. Supply a metric that returns a score and concise feedback. Keep the held-out set outside the search loop, checkpoint candidates, and preserve lineage. GEPA proposes and searches; validated scorers still own the objective. [Source](https://github.com/gepa-ai/gepa/blob/main/.claude/skills/gepa-optimize-anything/SKILL.md)
- **Braintrust:** Use experiment history and scorer evidence to compare proposed candidates, but keep optimizer feedback data separate from final validation data. [Source](https://www.braintrust.dev/docs)
- **Promptfoo:** Use a fixed regression config to compare exported candidates when the optimization engine itself is elsewhere. [Source](https://github.com/promptfoo/promptfoo/blob/main/plugins/promptfoo/skills/promptfoo-evals/SKILL.md)

Pin model and provider settings, set an explicit run budget, and verify current APIs before starting a paid search.
