#!/usr/bin/env node
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
if (args.length && (args.length !== 2 || args[0] !== "--results")) {
  console.error("usage: node eval/run.mjs [--results path]");
  process.exit(2);
}
const resultsPath = path.resolve(root, args[1] ?? "eval/baseline-results.json");
const kinds = ["positive", "negative", "ambiguous", "adversarial"];

async function json(file) {
  try {
    return JSON.parse(await readFile(file, "utf8"));
  } catch (error) {
    throw new Error(`${path.relative(root, file)}: ${error.message}`);
  }
}

function exactKeys(value, allowed, required, where) {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(`${where} must be an object`);
  const extra = Object.keys(value).filter((key) => !allowed.includes(key));
  const missing = required.filter((key) => !(key in value));
  if (extra.length) throw new Error(`${where} has unknown field(s): ${extra.join(", ")}`);
  if (missing.length) throw new Error(`${where} is missing field(s): ${missing.join(", ")}`);
}

function strings(value, where) {
  if (value === undefined) return [];
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string" || !item)) throw new Error(`${where} must be an array of non-empty strings`);
  if (new Set(value).size !== value.length) throw new Error(`${where} contains duplicate values`);
  return value;
}

function validateCase(item, source) {
  const where = `${source}:${item?.id ?? "<missing id>"}`;
  exactKeys(item, ["id", "skill", "kind", "request", "expect"], ["id", "skill", "kind", "request", "expect"], where);
  for (const key of ["id", "skill", "kind", "request"]) {
    if (typeof item[key] !== "string" || !item[key]) throw new Error(`${where}.${key} must be a non-empty string`);
  }
  if (!/^[a-z0-9-]+\.[a-z0-9-]+$/.test(item.id)) throw new Error(`${where}.id has invalid format`);
  if (!kinds.includes(item.kind)) throw new Error(`${where}.kind must be one of ${kinds.join(", ")}`);
  exactKeys(item.expect, ["activation", "actions", "output"], ["activation"], `${where}.expect`);
  if (!["required", "forbidden", "allowed"].includes(item.expect.activation)) throw new Error(`${where}.expect.activation is invalid`);
  if (item.expect.actions !== undefined) exactKeys(item.expect.actions, ["required", "forbidden"], [], `${where}.expect.actions`);
  if (item.expect.output !== undefined) exactKeys(item.expect.output, ["contains", "forbidden", "matches"], [], `${where}.expect.output`);
  const actionChecks = [
    ...strings(item.expect.actions?.required, `${where}.expect.actions.required`),
    ...strings(item.expect.actions?.forbidden, `${where}.expect.actions.forbidden`),
  ];
  const outputChecks = [
    ...strings(item.expect.output?.contains, `${where}.expect.output.contains`),
    ...strings(item.expect.output?.forbidden, `${where}.expect.output.forbidden`),
    ...strings(item.expect.output?.matches, `${where}.expect.output.matches`),
  ];
  if (!actionChecks.length && !outputChecks.length) throw new Error(`${where}.expect must assert an action or output invariant`);
  for (const pattern of item.expect.output?.matches ?? []) {
    try {
      new RegExp(pattern);
    } catch {
      throw new Error(`${where} has invalid regex ${JSON.stringify(pattern)}`);
    }
  }
}

function validateObservation(observed, where) {
  exactKeys(observed, ["activated", "actions", "output"], ["activated", "actions", "output"], where);
  if (typeof observed.activated !== "boolean") throw new Error(`${where}.activated must be boolean`);
  strings(observed.actions, `${where}.actions`);
  if (typeof observed.output !== "string") throw new Error(`${where}.output must be a string`);
}

function grade(test, observed) {
  const failures = [];
  const exp = test.expect;
  if (exp.activation === "required" && !observed.activated) failures.push("expected skill activation");
  if (exp.activation === "forbidden" && observed.activated) failures.push("forbidden skill activation occurred");
  for (const action of exp.actions?.required ?? []) if (!observed.actions.includes(action)) failures.push(`missing required action: ${action}`);
  for (const action of exp.actions?.forbidden ?? []) if (observed.actions.includes(action)) failures.push(`forbidden action occurred: ${action}`);
  for (const text of exp.output?.contains ?? []) if (!observed.output.includes(text)) failures.push(`output missing text: ${JSON.stringify(text)}`);
  for (const text of exp.output?.forbidden ?? []) if (observed.output.includes(text)) failures.push(`output contains forbidden text: ${JSON.stringify(text)}`);
  for (const pattern of exp.output?.matches ?? []) if (!new RegExp(pattern).test(observed.output)) failures.push(`output does not match /${pattern}/`);
  return failures;
}

try {
  const caseDir = path.join(root, "eval/cases");
  const files = (await readdir(caseDir)).filter((file) => file.endsWith(".json")).sort();
  if (!files.length) throw new Error("eval/cases has no JSON files");
  const cases = [];
  for (const file of files) {
    const value = await json(path.join(caseDir, file));
    if (!Array.isArray(value)) throw new Error(`eval/cases/${file} must contain an array`);
    for (const item of value) {
      validateCase(item, `eval/cases/${file}`);
      cases.push(item);
    }
  }
  const ids = new Set();
  for (const test of cases) {
    if (ids.has(test.id)) throw new Error(`duplicate case id: ${test.id}`);
    ids.add(test.id);
  }
  const skills = (await readdir(path.join(root, "skills"), { withFileTypes: true })).filter((entry) => entry.isDirectory()).map((entry) => entry.name).sort();
  for (const test of cases) if (!skills.includes(test.skill)) throw new Error(`${test.id}: unknown skill ${test.skill}`);
  for (const skill of skills) {
    const ownKinds = new Set(cases.filter((test) => test.skill === skill).map((test) => test.kind));
    for (const kind of kinds) if (!ownKinds.has(kind)) throw new Error(`${skill}: missing ${kind} case`);
  }
  const observations = await json(resultsPath);
  exactKeys(observations, [...ids], [...ids], path.relative(root, resultsPath));
  for (const [id, observation] of Object.entries(observations)) validateObservation(observation, `${path.relative(root, resultsPath)}:${id}`);

  let failed = 0;
  for (const test of cases) {
    const failures = grade(test, observations[test.id]);
    if (failures.length) {
      failed++;
      console.error(`FAIL ${test.id} (${test.skill}, ${test.kind})`);
      console.error(`  request: ${test.request}`);
      for (const failure of failures) console.error(`  - ${failure}`);
    } else {
      console.log(`PASS ${test.id}`);
    }
  }
  console.log(`\n${cases.length - failed}/${cases.length} passed`);
  process.exitCode = failed ? 1 : 0;
} catch (error) {
  console.error(`ERROR ${error.message}`);
  process.exitCode = 2;
}
