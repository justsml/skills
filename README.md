# AI Skillz

Opinionated agent skills for evaluating AI systems, exploring hard problems, and writing like a person.

Each skill packages a repeatable workflow in a `SKILL.md` file. See the [official OpenAI guide to skills](https://learn.chatgpt.com/docs/build-skills) for the format and how agents use them.

## Install

Run the interactive installer:

```bash
npx skills@latest add justsml/skills
```

Preview the available skills without installing:

```bash
npx skills@latest add justsml/skills --list
```

Or install one directly:

```bash
npx skills@latest add justsml/skills --skill unslop
```

Then invoke it by name:

```text
Use $unslop to make this launch post sound like a real person wrote it.
```

## Pick a skill

| Skill | Use it when you want to... | Try asking... |
| --- | --- | --- |
| [`unslop`](./skills/unslop/SKILL.md) | Remove stiff, generic AI writing without losing the original meaning | `Use $unslop to rewrite this README intro.` |
| [`council-of-dans`](./skills/council-of-dans/SKILL.md) | Get several independent approaches and combine the strongest parts | `Use $council-of-dans to pressure-test this API design.` |
| [`eval-expert`](./skills/eval-expert/SKILL.md) | Build and run a complete evaluation program for an AI feature | `Use $eval-expert to design evals for our support bot.` |
| [`eval-doctor`](./skills/eval-doctor/SKILL.md) | Audit an eval stack against current provider and platform guidance | `Use $eval-doctor to find the highest-value upgrades in our eval stack.` |


## Thanks

This repository started with inspiration from [Matt Pocock's skills collection](https://github.com/mattpocock/skills) and evaluation work published by [LLM Judge](https://github.com/wenxuec/llm-judge), [EvalSurfer](https://github.com/di37/EvalSurfer), [agent-eval](https://github.com/ericrisco/rsc-harness/tree/main/skills/agent-eval), [deepeval-bcg](https://github.com/EvXata/deepeval-bcg), [skillquarium](https://github.com/stanfish06/skillquarium), [Phoenix](https://github.com/Arize-ai/phoenix), [GEPA](https://github.com/gepa-ai/gepa), [Braintrust](https://github.com/braintrustdata/eval-library), [Promptfoo](https://github.com/promptfoo/promptfoo), and [LangSmith](https://github.com/langchain-ai/langsmith-skills). Thanks to their authors and contributors for sharing the projects that helped shape these skills.
