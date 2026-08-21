# Platform notes for trace mining

- **Phoenix:** Choose trace, session, or span as the unit first. Sample records, record concrete open-coding observations, then consolidate them through axial coding. Use a coding-run ID and reversible local sidecar. Remote annotation writes need explicit approval. [Source](https://github.com/Arize-ai/phoenix/blob/main/.agents/skills/phoenix-cli/SKILL.md)
- **LangSmith:** Inspect an actual run and trace schema before writing extraction code. Use bounded time and metadata filters. Keep offline dataset evaluators distinct from online project evaluators. [Source](https://github.com/langchain-ai/langsmith-skills/blob/main/config/skills/langsmith-evaluator/SKILL.md)

Export only the fields needed to reproduce the failure. Document sampling bias and get explicit approval before querying or uploading private traces at broad scope.
