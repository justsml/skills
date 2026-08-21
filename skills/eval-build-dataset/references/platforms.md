# Platform notes for eval datasets

- **Braintrust:** Preserve stable external case IDs and split metadata when creating a hosted dataset. Record the hosted dataset and version in experiment manifests. [Source](https://www.braintrust.dev/docs)
- **LangSmith:** Inspect a real example schema before import. Preserve trace and example IDs when promoting runs into a dataset. [Source](https://github.com/langchain-ai/langsmith-skills/blob/main/config/skills/langsmith-evaluator/SKILL.md)
- **Langfuse:** Preserve caller-owned item IDs plus `source_trace_id` and `source_observation_id` when promoting reviewed failures. Pin the dataset version timestamp for runs and store the JSON Schema separately because item mutations create versions but schema changes do not. Archive excludes an item from future runs; upserting an existing ID mutates shared data. Verify version pinning against the installed SDK because current experiment pages disagree. [Datasets](https://langfuse.com/docs/evaluation/experiments/datasets) [SDK experiments](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
- **Phoenix:** Treat trace annotations and coding sidecars as discovery evidence. Review and export selected examples before they become ground truth. [Source](https://github.com/Arize-ai/phoenix/blob/main/.agents/skills/phoenix-cli/SKILL.md)
- **Promptfoo:** Keep durable cases outside provider-specific config when portability matters, then generate or reference test entries from the versioned source. [Source](https://github.com/promptfoo/promptfoo/blob/main/plugins/promptfoo/skills/promptfoo-evals/SKILL.md)

Hosted imports may transmit private inputs and outputs. Get explicit approval for private or broad uploads.
