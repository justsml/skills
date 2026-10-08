# AI Skillz

Opinionated agent skills for evaluating AI systems, tuning software performance, operating remote compute, exploring hard problems, and writing like a person.

Current package version: **1.1.0**. See the [mini changelog](#changelog) for what's new.

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

## Check skill behavior

Check the skills against their cases offline, without credentials or network access:

```bash
npm run eval
```

This grades the hand-written observations in `eval/baseline-results.json` against the cases in `eval/cases/*.json`. It is a fixture check: it catches cases and skills that have drifted apart, and proves nothing about model behavior.

Probe skill selection against a real model:

```bash
npm run eval:live
```

The routing probe uses GPT-6.1 Sol by default; GPT-6 Luna and Claude Sonnet 5.5 are selectable with `--model`. It checks skill descriptions, not agent task execution. OpenAI models need `OPENAI_API_KEY`; Sonnet needs `ANTHROPIC_API_KEY`. Every run saves raw evidence and model-specific cost estimates. Run `npm run eval:validate` for metadata checks and `npm run eval:test` for runner tests. See [`eval/README.md`](./eval/README.md) for usage and native Codex/Claude evaluation guidance, and the [council review](./docs/research/eval-setup-review.md) for findings.

## Pick a skill

| Skill | Use it when you want to... | Try asking... |
| --- | --- | --- |
| [`unslop`](./skills/unslop/SKILL.md) | Remove stiff, generic AI writing without losing the original meaning | `Use $unslop to rewrite this README intro.` |
| [`council-of-dans`](./skills/council-of-dans/SKILL.md) | Run the same task in parallel under different priorities and see every result (name it explicitly — it never self-invokes) | `Use $council-of-dans to pressure-test this API design.` |
| [`eval-expert`](./skills/eval-expert/SKILL.md) | Build and run a complete evaluation program for an AI feature | `Use $eval-expert to design evals for our support bot.` |
| [`eval-doctor`](./skills/eval-doctor/SKILL.md) | Audit an eval stack against current provider and platform guidance | `Use $eval-doctor to find the highest-value upgrades in our eval stack.` |
| [`remote-compute`](./skills/remote-compute/SKILL.md) | Configure CPU/GPU workers, compare providers, check balances and usage, or run bounded remote jobs | `Use $remote-compute setup for this project, then compare GPU options within a $10 run budget.` |
| [`auto-tune-performance`](./skills/auto-tune-performance/SKILL.md) | Profile bottlenecks, test minimal implementations and tuning parameters, and verify gains without sacrificing correctness | `Use $auto-tune-performance to improve this app's p95 latency while preserving behavior and a $20 experiment budget.` |

## Performance tuning

[`auto-tune-performance`](./skills/auto-tune-performance/SKILL.md) turns [Give Your Agent a Profiler](https://danlevy.net/performance-tuning-with-an-agent/) into a bounded tuning workflow: prove useful work, locate the limiting resource, test a hypothesis, reject regressions, and confirm the finalist with fresh measurements. It applies to browsers, services, CPU/I/O, GPU/model serving, builds, and performance-sensitive agent instructions.

It considers a minimal implementation or clean experimental rebuild by default, checks load-bearing pieces through subtraction/add-back, and maps useful parameters before searching. Project priorities and rerun recipes persist in the target project's performance record. When gains stall, it presents architectural or requirement tradeoffs; when work can be partitioned, it can use available remote-compute workflows for bounded fleets.

The optional Node/Python helper compares positive metrics from independent paired blocks and reports `accept`, `reject`, `keep_baseline`, `inconclusive`, or `needs_confirmation`. It includes approximate adjusted bootstrap intervals and hard correctness gates; it does not run workloads or certify their measurement design. See [measurement design](./skills/auto-tune-performance/references/measurement.md), [comparison format](./skills/auto-tune-performance/references/decisions.md), and the [source analysis](./docs/research/auto-tune-performance-source-analysis.md).

The separate [web-performance playbook](./skills/auto-tune-performance/references/web-performance.md) covers 60 FPS and higher-refresh frame budgets, actual GPU/renderer verification, visual recordings, keyboard/scroll/history stress, and targeted Lighthouse, payload, JS/CSS coverage and CDN diagnostics. Every platform uses a concise summary of checks, proved findings, supported suspicions and missing evidence.

Try `Use $auto-tune-performance to check the app's performance again.` The skill reuses the project's last matching recipe and priorities, then collects fresh measurements. It explains missing tools/access, checks correctness and visual behavior, and proposes explicit architectural tradeoffs when worthwhile gains stall.

```bash
# Choose one entry point for the same JSON contract:
node skills/auto-tune-performance/scripts/compare.mjs /path/to/experiment.json
python3 skills/auto-tune-performance/scripts/compare.py /path/to/experiment.json
bash skills/auto-tune-performance/scripts/compare.sh /path/to/experiment.json
npm run helpers:test
python3 -m unittest discover -s skills/auto-tune-performance/scripts -p 'test_*.py'
```

## Remote compute

Invoke `$remote-compute setup`, `$remote-compute status`, or `$remote-compute run <workload>` in your agent. The skill also applies to remote builds, large evals/imports, and private model hosting; it can offer remote capacity when a substantial job is constrained locally.

Policy, provider choices, constraints, and authorization belong to each project's `.remote-compute/` directory, even with a global skill install. Setup scaffolds local files and guides provider onboarding; it does not rent a machine. Status refreshes configured providers through their official tools and reports inventory/billing coverage, balances, recent usage, attributed run/thread spend, and cost forecasts. Run coordinates bounded jobs and verified cleanup under the project's permission.

The bundled helpers need no packages or network access. Choose installed **Node 20+** or **Python 3.10+**; **Bash 3.2+** entry points automatically select Node, then Python. Bash is a dispatcher, not a standalone arithmetic implementation. From this checkout:

```bash
# Node equivalents accept the same setup/status/estimate arguments:
node skills/remote-compute/scripts/remote_compute.mjs setup --project /absolute/project
bash skills/remote-compute/scripts/remote_compute.sh status --project /absolute/project
python3 skills/remote-compute/scripts/remote_compute.py setup --project /absolute/project
python3 skills/remote-compute/scripts/remote_compute.py status --project /absolute/project
python3 skills/remote-compute/scripts/remote_compute.py estimate --rate-low 0.50 --rate-high 0.80 --hours-low 1 --hours-high 5
python3 -m unittest discover -s skills/remote-compute/scripts -p 'test_*.py'
```

The helper's status is a **saved-observation report**, not a cloud scanner or watchdog. Live operations use available provider CLIs/APIs/connectors; the agent verifies those operations and cleanup before paid admission. Estimates include 1–5 additional hours and an unchanged-fleet 24-hour scenario, with stale/unknown costs kept explicit. See [project configuration](./skills/remote-compute/references/project-config.md), [provider setup paths](./skills/remote-compute/references/providers.md), and the [extraction review](./docs/research/remote-compute-extraction.md).

Agents probe runtime availability/version before choosing a helper, record the interpreter with the result, and retain the same input files, schema and exit-code meanings. A validation failure is not a reason to retry through another runtime. No runtime is installed merely to invoke these optional helpers. Node/Python comparisons share seeded bootstrap draws; floating-point outputs can differ slightly, so retain the chosen runtime for a whole experiment.

See the [final critical review](./docs/research/compute-performance-review.md) for fixes, runtime checks and evidence limits.

Both new skills can be invoked by name or selected implicitly for relevant work. Global installation keeps project budgets, permissions, preferences and run records in the target project. Installing a skill or configuring credentials does not authorize paid resources; setup defaults to no paid authorization.

## Changelog

### 1.1.0 — 2026-10-07

- Added `remote-compute`: project setup, provider/status and balance guidance, CPU/GPU workers, private models, cost forecasts and verified cleanup.
- Added `auto-tune-performance`: profiling, minimal-baseline/add-back experiments, parameter tuning, saved rerun recipes and architectural/scaling alternatives.
- Added a dedicated web playbook for frame pacing, visual/keyboard/navigation checks, payloads, coverage and CDN diagnostics.
- Added dependency-free Node/Python helpers and Bash runtime dispatchers for remote configuration/status estimates and paired performance comparisons with correctness and regression gates.
- Updated evaluation tooling with metadata validation, deterministic runner tests, model-specific routing receipts and explicit evidence limits.

## Thanks

This repository started with inspiration from [Matt Pocock's skills collection](https://github.com/mattpocock/skills) and evaluation work published by [LLM Judge](https://github.com/wenxuec/llm-judge), [EvalSurfer](https://github.com/di37/EvalSurfer), [agent-eval](https://github.com/ericrisco/rsc-harness/tree/main/skills/agent-eval), [deepeval-bcg](https://github.com/EvXata/deepeval-bcg), [skillquarium](https://github.com/stanfish06/skillquarium), [Phoenix](https://github.com/Arize-ai/phoenix), [GEPA](https://github.com/gepa-ai/gepa), [Braintrust](https://github.com/braintrustdata/eval-library), [Promptfoo](https://github.com/promptfoo/promptfoo), and [LangSmith](https://github.com/langchain-ai/langsmith-skills). Thanks to their authors and contributors for sharing the projects that helped shape these skills.
