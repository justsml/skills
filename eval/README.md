# Behavioral evaluations

Fixture checks, synthetic routing, structural validation, and native agent execution measure different things.

## Offline checks for the current collection

These commands need no provider credentials or paid calls:

```bash
npm run eval:validate
npm run eval:test
npm run eval
npm run helpers:test
python3 -m unittest discover -s skills/remote-compute/scripts -p 'test_*.py'
python3 -m unittest discover -s skills/auto-tune-performance/scripts -p 'test_*.py'
```

The Node/Python helper tests exercise local scaffolding/accounting and paired-comparison decisions. Node tests include Bash dispatch and cross-runtime parity when Python is available (otherwise parity is explicitly skipped). They do not provision a provider, enforce a watchdog, drive a browser or validate an agent's tuning quality. The collection's contract fixtures include remote budget/credential boundaries, repeat performance recipes, minimal/add-back experiments, scaling/architecture choices, and web visual/input/navigation/coverage/delivery cases. Real task execution remains a separate evidence layer.

See [remote compute configuration](../skills/remote-compute/references/project-config.md), [performance comparison format](../skills/auto-tune-performance/references/decisions.md), and the [web-performance playbook](../skills/auto-tune-performance/references/web-performance.md) for the executable helper formats and workflow requirements.

## `npm run eval` — offline contract check

- `cases/*.json` describes requests and gradeable expectations.
- `baseline-results.json` records hand-written observations of the behavior each case wants.
- `run.mjs` validates the files and grades every observation.

```bash
npm run eval
```

**This is a fixture check, not a model test.** The checked-in observations were written to satisfy the cases, so this suite passes by construction. Its job is to keep the cases and the skills describing the same contract: when you change what a skill does, this run tells you which expectations and fixtures went stale. It proves nothing about how a model behaves.

To grade a real agent run, write one observation per case to another JSON file and pass it to the same runner:

```bash
node eval/run.mjs --results /path/to/results.json
```

A runtime adapter or trace reviewer can consume each case's `request`, record whether the agent loaded the skill, list its action tags, capture its output, and pass those observations in.

## `npm run eval:live` — routing check against a real model

```bash
npm run eval:live               # every case
node eval/live.mjs --limit 6    # first 6 cases
node eval/live.mjs --case unslop.debug-code
```

Uses GPT-6.1 Sol by default. The allowlisted alternatives are GPT-6 Luna and Claude Sonnet 5.5:

```bash
node eval/live.mjs --model gpt-6-luna --limit 6
node eval/live.mjs --model claude-sonnet-5-5 --limit 6
node eval/live.mjs --dry-run --limit 6
node --test eval/live.test.mjs
```

OpenAI models use the Responses API and `OPENAI_API_KEY`; Sonnet uses the Messages API and `ANTHROPIC_API_KEY`. CLI subscription login does not authenticate these direct API calls. No provider fallback or retries are enabled. Unknown model IDs are rejected before spending. OpenAI requests set `store: false` and standard service tier. GPT models use low reasoning effort; Sonnet uses `between_tools` to avoid upfront thinking. Temperature is omitted because Sonnet 5.5 rejects nondefault sampling controls. The output budget is 2,048 tokens because GPT reasoning consumes that budget along with the short visible answer; adjust with `--max-tokens` (1–8,192). An exhausted budget fails the case.

This is a **synthetic description-routing probe**. It provides one catalog and asks for one skill name or `none`. It does not load full skill instructions, execute tools, discover installed plugins, reproduce either host's skill resolver, or prove task success. The manual-only label intentionally approximates a rule: Claude Code actually removes those descriptions from model context, and explicit invocation runs the skill through the host. Treat this probe as a quick comparison of descriptions, then verify actual activation and behavior in each target harness.

`required` must choose the named skill; `forbidden` must not choose it; valid `allowed` choices are informational and excluded from the scored pass denominator. Empty, unknown, explanatory, refused, and truncated output fails, including on negative cases. A forbidden case still permits a different valid skill: it only asserts the target skill stays inactive.

Every live run writes an evidence envelope under `eval/results/` (or `--out`): model/provider, timestamps, parameters, prompt, selected cases, source content hashes, git state, raw output and usage, returned model, request/response IDs, stop reasons, coverage, summary, and estimated cost. Partial runs print selected/total coverage. `fullSelection` means all case IDs were selected; the separate `coverage` counts completed, valid, and errored responses. It does not imply every selected request succeeded. API errors are stored per case and yield exit code 2; grading failures yield 1. Missing usage makes cost incomplete because failed requests may still be billed. Artifacts contain task text, so review before sharing. Rates are an October 7, 2026 snapshot, use each chosen model's published input/cache-read/output prices, and are estimates rather than invoices. Check current provider billing for changes or additional cache-write charges.

## Release evidence across agent and plugin hosts

Keep three layers separate: offline case/fixture validation, this synthetic routing probe, and actual task execution. A release claim needs the third layer. Install the skill or plugin in an isolated project using the target host's supported layout, validate packaging, invoke realistic cases, and retain native traces and resulting files. Test both implicit activation and explicit invocation, nonactivation on adjacent requests, tool/action constraints, and the observable result. Record host CLI version, model, skill revision, permissions and available tools so results can be replayed. Avoid ambient user skills and credentials in the sandbox; mock external effects in fixtures.

Use a stable held-out task set with positive, negative, ambiguous and adversarial cases; add regressions from real failures separately from examples used to edit descriptions. Compare revisions on identical cases and repeat borderline/stochastic cases. Prefer file state, test outcomes and captured tool events over a model's claim that it acted. Calibrate any LLM judge against blinded human labels and keep model-specific results separate. Static baseline rows and canned persona examples are development fixtures, not independent evidence.

Current host differences matter. [Claude Code skill docs](https://code.claude.com/docs/en/skills) describe native invocation restrictions and recommend `claude plugin validate` plus plugin evals when packaged as a plugin. [Codex skill docs](https://developers.openai.com/codex/skills) describe Codex discovery, metadata and explicit invocation; test that installation separately rather than translating a Claude-only flag into a claimed Codex guarantee. This repository currently has a skill collection, not evidence that a publishable plugin manifest or native agent execution adapter has been validated.

Model parameter and pricing sources: [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview), and [Sonnet migration details](https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5).

## Council persona examples

`datasets/council-of-dans-personas.json` contains one-shot prompts, example candidate outputs, and rationale labels covering every built-in council persona. The examples span code generation, architecture, and security analysis so adherence is not conflated with one task shape.

`scorers/council-of-dans-persona.mjs` builds a reference-free LLM-judge prompt with asymmetric evidence requirements for each persona. It separately scores task completion and persona adherence; an incomplete artifact receives zero even if its voice resembles the persona. Use deterministic sampling only when the selected judge supports it (Sonnet 5.5 rejects nondefault temperature); retain the raw JSON and judge model/version, and calibrate the scorer against blinded human labels before using it as a release gate.

Run its deterministic contract tests with:

```bash
node --test eval/scorers/council-of-dans-persona.test.mjs
```

## Add a case

Add an object to any JSON file in `cases/`. The runner discovers it automatically. Each case has this shape:

```json
{
  "id": "skill.unique-name",
  "skill": "skill-directory-name",
  "kind": "positive | negative | ambiguous | adversarial",
  "request": "The user request presented to the agent",
  "expect": {
    "activation": "required | forbidden | allowed",
    "actions": { "required": ["action-tag"], "forbidden": ["action-tag"] },
    "output": { "contains": ["text"], "forbidden": ["text"], "matches": ["regex"] }
  }
}
```

Action tags describe observable steps at the agent boundary, such as `browse-official-docs` or `edit-prose`. Matching is case-sensitive. Regex strings use JavaScript syntax.

The results file is a JSON object keyed by case ID:

```json
{
  "skill.unique-name": {
    "activated": true,
    "actions": ["action-tag"],
    "output": "Agent-visible result"
  }
}
```

The runner rejects unknown fields, duplicate IDs, malformed regular expressions, missing observations, observations without cases, and incomplete coverage. Every skill needs positive, negative, ambiguous, and adversarial cases.

## Structural and native-harness checks


Run `npm run eval:validate` before spending on model calls. It checks skill metadata, name/directory alignment, unique fields and instructions, and reports differences between Claude frontmatter invocation policy and Codex `agents/openai.yaml`. The parser supports the repository's single-line scalars and rejects unsupported multiline YAML. The `eval-expert` policy currently disables Codex implicit invocation but allows Claude implicit invocation; review this deliberate-or-accidental difference before changing its contract.

For actual behavior, use isolated task workspaces with fixture inputs, controlled tools and mocked external services, and compare the same tasks with and without the skill. Keep discovery/trigger tests separate from explicit invocation tests. Retain harness version, model, full instructions, raw trace, output artifacts, scorer version and usage for each trial. Required action tags need a trace reviewer or executable tool/artifact check; self-reported model tags alone are not proof. Report failure and informational denominators per skill and case kind. Calibration against blinded human labels, repeated trials and a held-out set precede release gating.

Claude Code provides native `claude plugin eval` with an isolated with/without baseline, rubric grading, mocks and CI thresholds. This repository currently contains loose skills, not a plugin; package and validate a real plugin before using that seam. A validator that returns an empty component list does not validate these loose skills. When using native eval, override **both** `--model claude-sonnet-5-5` and `--judge-model claude-sonnet-5-5`: the installed CLI otherwise defaults the judge to Haiku. Use `--no-publish` and an explicit `--max-cost-usd` for a bounded local experiment. Do not automatically execute adversarial paid-host or secret-transfer requests against real credentials.

For Codex, install only the skills under test in an isolated `.agents/skills/` workspace and capture `codex exec --json` evidence. Test `$skill-name` explicit invocation separately from implicit selection. CLI invocation alone is not proof that the intended skill loaded or that its steps executed. This change provides structural/proxy checks and a migration path; it does not claim native-harness behavior has been measured.

Official guidance checked 2026-10-07: [Codex skills](https://developers.openai.com/codex/skills/), [Claude Code skills and evaluation](https://code.claude.com/docs/en/skills), [Claude plugins](https://code.claude.com/docs/en/plugins), [Sonnet 5.5 request changes](https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5), [Sonnet 5.5 pricing](https://platform.claude.com/docs/en/models/sonnet-5-5/overview).
