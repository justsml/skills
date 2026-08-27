import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { buildPersonaJudgePrompt, parsePersonaJudgeResult, PERSONAS } from "./council-of-dans-persona.mjs";

const rows = JSON.parse(await readFile(new URL("../datasets/council-of-dans-personas.json", import.meta.url), "utf8"));

test("dataset covers every council persona with a concrete example", () => {
  assert.deepEqual(new Set(rows.map((row) => row.persona)), new Set(PERSONAS));
  for (const row of rows) {
    assert.ok(row.prompt.length > 20);
    assert.ok(row.exampleOutput.length > 250);
    assert.equal(row.whyItFits.length, 3);
  }
});

test("judge prompt is asymmetric across personas", () => {
  const row = rows.find(({ persona }) => persona === "Systems Architect");
  const architect = buildPersonaJudgePrompt({ ...row, output: row.exampleOutput });
  const doomsayer = buildPersonaJudgePrompt({ ...row, persona: "Doomsayer", output: row.exampleOutput });
  assert.match(architect, /boundaries and component responsibilities/);
  assert.match(architect, /invariants or interface contracts/);
  assert.doesNotMatch(architect, /blast radius/);
  assert.match(doomsayer, /blast radius/);
  assert.match(doomsayer, /tripwires/);
  assert.notEqual(architect, doomsayer);
});

test("judge cannot award persona adherence to an incomplete artifact", () => {
  const scored = parsePersonaJudgeResult({ task_completion: 1, persona_adherence: 4, evidence: ["strong lens"], missing: ["requested artifact"] });
  assert.equal(scored.score, 0);
});

test("valid complete score is normalized", () => {
  const scored = parsePersonaJudgeResult('{"task_completion":4,"persona_adherence":3,"evidence":["a","b"],"missing":["c"]}');
  assert.equal(scored.score, 0.75);
});

test("malformed judge output is rejected", () => {
  assert.throws(() => parsePersonaJudgeResult({ task_completion: 4, persona_adherence: 5, evidence: [], missing: [] }), /persona_adherence/);
});
