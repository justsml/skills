# Behavioral evaluations

The evaluation suite separates test intent from observed agent behavior:

- `cases/*.json` describes requests and gradeable expectations.
- `baseline-results.json` records the current offline baseline.
- `run.mjs` validates the files and grades every observation.

Run the repository baseline with:

```bash
npm run eval
```

To grade a fresh agent run, write one observation per case to another JSON file and pass it to the same runner:

```bash
node eval/run.mjs --results /path/to/results.json
```

The checked-in observations provide a visible, deterministic baseline. They do not prove that every model follows the skills reliably. A runtime adapter or trace reviewer can consume each case's `request`, record whether the agent loaded the skill, list its action tags, capture its output, and pass those observations to the runner.

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
