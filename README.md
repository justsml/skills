# AI Skillz

Reusable instructions that teach coding agents how to do specialized work.

If you have ever wished your AI assistant had a repeatable playbook for evaluating an AI feature, getting a second opinion, or cleaning up robotic prose, this repo is for you.

No library imports. No API keys. Pick a skill, install it, and ask your agent to use it.

## Wait, what is a skill?

A skill is a folder containing a `SKILL.md` file. That file gives an AI coding agent a focused set of instructions for a particular job.

Think of it like a reusable checklist for your agent:

```text
you ask for a task
        |
        v
the agent loads the matching skill
        |
        v
the agent follows its process
```

Skills do not add new software to your app. They improve how a compatible agent approaches the work you give it.

## Quick start

You need [Node.js](https://nodejs.org/) and `npx`. Then run:

```bash
npx skills@latest add justsml/skills
```

The installer lets you choose which skills to add and where to install them.

Want to look before installing anything?

```bash
npx skills@latest add justsml/skills --list
```

Already know which one you want? Install it by name:

```bash
npx skills@latest add justsml/skills --skill unslop
```

Once installed, mention the skill in your prompt. For example:

```text
Use $unslop to make this launch post sound like a real person wrote it.
```

Your agent may use a slightly different way to invoke skills. Check its skill documentation if `$skill-name` does not work.

## Pick a skill

| Skill | Use it when you want to... | Try asking... |
| --- | --- | --- |
| [`unslop`](./skills/unslop/SKILL.md) | Remove stiff, generic AI writing without losing the original meaning | `Use $unslop to rewrite this README intro.` |
| [`council-of-dans`](./skills/council-of-dans/SKILL.md) | Get several independent approaches and combine the strongest parts | `Use $council-of-dans to pressure-test this API design.` |
| [`eval-expert`](./skills/eval-expert/SKILL.md) | Build and run a serious evaluation program for an AI feature | `Use $eval-expert to design evals for our support bot.` |
| [`eval-doctor`](./skills/eval-doctor/SKILL.md) | Audit an eval stack against current provider and platform guidance | `Use $eval-doctor to find the highest-value upgrades in our eval stack.` |

Not sure where to start? Install `unslop`. It is small, easy to see in action, and useful on almost any writing task.

## Common questions

### Does this change my project?

Installing a skill adds instructions to your AI agent's skill directory. It does not add a runtime dependency to the app you are building.

### Can I read a skill before using it?

Yes. Every skill is plain Markdown. Click a skill in the table above and read its `SKILL.md` file.

### Can I install only one skill?

Yes. Use `--skill` followed by its name:

```bash
npx skills@latest add justsml/skills --skill eval-expert
```

### Why didn't my agent use the skill?

Try naming it directly in your prompt, such as `Use $unslop to...`. Also confirm that your agent supports skills and that the installer placed the skill in the correct directory.

## Working on this repo

Clone the repo, then list the skills it contains:

```bash
git clone https://github.com/justsml/skills.git
cd skills
./scripts/list-skills.sh
```

To test local edits, symlink all repo skills into the common Claude, Codex, and agent skill directories on your machine:

```bash
./scripts/link-skills.sh
```

Heads up: the link script replaces an existing non-symlinked skill folder when it has the same name as a repo skill. Check those destinations first if you have local skills you want to keep.

## Adding a skill

1. Create `skills/your-skill-name/SKILL.md`.
2. Add `skills/your-skill-name/agents/openai.yaml` if the skill needs display metadata or an invocation policy.
3. Add the skill to the table in this README.
4. Run `./scripts/list-skills.sh` and make sure it appears.

Keep each skill directly under `skills/`. Do not add category folders between `skills/` and the skill itself.
