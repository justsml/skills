#!/usr/bin/env node
// Live routing eval: given only the skill descriptions, does a real model pick
// the right skill for each case request? This is the cheapest test that touches
// a model and still measures something real — the descriptions are what decides
// whether a skill ever loads.
//
//   node eval/live.mjs                 # every case
//   node eval/live.mjs --limit 6       # first 6 cases
//   node eval/live.mjs --case unslop.debug-code
//   node eval/live.mjs --out /tmp/choices.json
import { readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MODEL = "claude-haiku-4-5";
const PRICE_PER_MTOK = { input: 1, output: 5 };
const CONCURRENCY = 4;
const MAX_TOKENS = 16;

function parseArgs(argv) {
  const out = { limit: Infinity, case: null, out: null, model: MODEL };
  for (let i = 0; i < argv.length; i += 2) {
    const [flag, value] = [argv[i], argv[i + 1]];
    if (!value) throw new Error(`${flag} needs a value`);
    if (flag === "--limit") out.limit = Number(value);
    else if (flag === "--case") out.case = value;
    else if (flag === "--out") out.out = value;
    else if (flag === "--model") out.model = value;
    else throw new Error(`unknown flag ${flag}`);
  }
  if (!Number.isFinite(out.limit) && out.limit !== Infinity) throw new Error("--limit must be a number");
  return out;
}

function frontmatter(text) {
  const match = /^---\n([\s\S]*?)\n---/.exec(text);
  if (!match) return {};
  const fields = {};
  for (const line of match[1].split("\n")) {
    const kv = /^([a-z-]+):\s*(.*)$/.exec(line);
    if (kv) fields[kv[1]] = kv[2].replace(/^["']|["']$/g, "");
  }
  return fields;
}

async function loadCatalog() {
  const dirs = (await readdir(path.join(root, "skills"), { withFileTypes: true }))
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
  const skills = [];
  for (const dir of dirs) {
    const fields = frontmatter(await readFile(path.join(root, "skills", dir, "SKILL.md"), "utf8"));
    if (!fields.description) throw new Error(`skills/${dir}/SKILL.md has no description`);
    skills.push({
      name: fields.name ?? dir,
      description: fields.description,
      manualOnly: fields["disable-model-invocation"] === "true",
    });
  }
  return skills;
}

async function loadCases() {
  const dir = path.join(root, "eval/cases");
  const files = (await readdir(dir)).filter((file) => file.endsWith(".json")).sort();
  const cases = [];
  for (const file of files) cases.push(...JSON.parse(await readFile(path.join(dir, file), "utf8")));
  return cases;
}

function systemPrompt(skills) {
  const catalog = skills
    .map((skill) => `- ${skill.name}${skill.manualOnly ? " (loads only when the user names it)" : ""}: ${skill.description}`)
    .join("\n");
  return [
    "You are an agent deciding which skill, if any, to load before answering a request.",
    "",
    "Available skills:",
    catalog,
    "",
    `Reply with exactly one skill name from the list, or the single word none. Output nothing else.`,
  ].join("\n");
}

async function pool(items, size, worker) {
  const results = new Array(items.length);
  let next = 0;
  await Promise.all(
    Array.from({ length: Math.min(size, items.length) }, async () => {
      while (next < items.length) {
        const index = next++;
        results[index] = await worker(items[index]);
      }
    }),
  );
  return results;
}

let Anthropic;
try {
  ({ default: Anthropic } = await import("@anthropic-ai/sdk"));
} catch {
  console.error("ERROR @anthropic-ai/sdk is not installed. Run: npm install");
  process.exit(2);
}

try {
  const args = parseArgs(process.argv.slice(2));
  const skills = await loadCatalog();
  const names = new Set(skills.map((skill) => skill.name));
  let cases = await loadCases();
  if (args.case) {
    cases = cases.filter((test) => test.id === args.case);
    if (!cases.length) throw new Error(`no case with id ${args.case}`);
  }
  cases = cases.slice(0, args.limit);

  const client = new Anthropic();
  const system = systemPrompt(skills);
  const usage = { input: 0, output: 0 };

  const observations = await pool(cases, CONCURRENCY, async (test) => {
    const response = await client.messages.create({
      model: args.model,
      max_tokens: MAX_TOKENS,
      temperature: 0,
      system,
      messages: [{ role: "user", content: test.request }],
    });
    usage.input += response.usage.input_tokens;
    usage.output += response.usage.output_tokens;
    const text = response.content
      .filter((block) => block.type === "text")
      .map((block) => block.text)
      .join("")
      .trim()
      .toLowerCase();
    const chosen = names.has(text) ? text : "none";
    return { id: test.id, skill: test.skill, activation: test.expect.activation, chosen, raw: text };
  });

  let failed = 0;
  for (const observation of observations) {
    const activated = observation.chosen === observation.skill;
    let verdict = "PASS";
    if (observation.activation === "required" && !activated) verdict = "FAIL";
    if (observation.activation === "forbidden" && activated) verdict = "FAIL";
    if (observation.activation === "allowed") verdict = "INFO";
    if (verdict === "FAIL") failed++;
    console.log(`${verdict} ${observation.id} (want ${observation.activation}, chose ${observation.chosen})`);
  }

  const cost = (usage.input * PRICE_PER_MTOK.input + usage.output * PRICE_PER_MTOK.output) / 1e6;
  console.log(`\n${observations.length - failed}/${observations.length} passed on ${args.model}`);
  console.log(`${usage.input} input + ${usage.output} output tokens, about $${cost.toFixed(4)}`);
  if (args.out) {
    await writeFile(path.resolve(root, args.out), `${JSON.stringify(observations, null, 2)}\n`);
    console.log(`choices written to ${args.out}`);
  }
  process.exitCode = failed ? 1 : 0;
} catch (error) {
  console.error(`ERROR ${error.message}`);
  if (/authentication/i.test(error.message)) console.error("Set ANTHROPIC_API_KEY, or run `ant auth login`.");
  process.exitCode = 2;
}
