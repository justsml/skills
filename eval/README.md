# Behavioral evaluations

Two runners, and they measure different things.

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

Sends each case request to Claude Haiku 4.5 with nothing but the skill names and descriptions, and asks which skill it would load. Grades the answer against `expect.activation`: `required` must select that skill, `forbidden` must not, `allowed` is reported without a verdict. Skills marked `disable-model-invocation` are labeled as manual-only in the catalog, so this also checks that they stay quiet on requests that do not name them.

This tests descriptions, which is what actually decides whether a skill ever loads. It is deliberately the cheapest real test available — one short reply per case, capped at 16 output tokens. The full suite is well under a cent, and the run prints its token usage and estimated cost. Needs `ANTHROPIC_API_KEY` or an `ant auth login` profile.

## Council persona examples

`datasets/council-of-dans-personas.json` contains one-shot prompts, example candidate outputs, and rationale labels covering every built-in council persona. The examples span code generation, architecture, and security analysis so adherence is not conflated with one task shape.

`scorers/council-of-dans-persona.mjs` builds a reference-free LLM-judge prompt with asymmetric evidence requirements for each persona. It separately scores task completion and persona adherence; an incomplete artifact receives zero even if its voice resembles the persona. Keep judge temperature at zero, retain the raw JSON and judge model/version, and calibrate the scorer against blinded human labels before using it as a release gate.

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
