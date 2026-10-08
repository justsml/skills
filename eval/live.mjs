#!/usr/bin/env node
// A synthetic, single-choice description-routing probe, not an agent execution eval.
import { readdir, readFile, writeFile, mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { metadata as skillMetadata } from './validate-skills.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const MODELS = Object.freeze({
  'gpt-6.1-sol': { provider: 'openai', input: 2, cachedInput: 0.1, cacheWrite: 2.5, output: 10, effort: 'low', source: 'https://developers.openai.com/api/docs/models/gpt-6.1-sol' },
  'gpt-6-luna': { provider: 'openai', input: 0.1, cachedInput: 0.01, cacheWrite: 0.125, output: 0.5, effort: 'low', source: 'https://developers.openai.com/api/docs/models/gpt-6-luna' },
  'claude-sonnet-5-5': { provider: 'anthropic', input: 2, cachedInput: 0.1, cacheWrite: 2.5, output: 10, effort: 'low', source: 'https://platform.claude.com/docs/en/models/sonnet-5-5/overview' },
});
export function parseArgs(argv) {
  const args = { limit: Infinity, case: null, out: null, model: 'gpt-6.1-sol', concurrency: 4, maxTokens: 2048, dryRun: false };
  const seen = new Set();
  for (let i = 0; i < argv.length; i++) {
    const flag = argv[i];
    if (seen.has(flag)) throw new Error(`duplicate flag ${flag}`);
    seen.add(flag);
    if (flag === '--dry-run') { args.dryRun = true; continue; }
    const fields = { '--limit': 'limit', '--case': 'case', '--out': 'out', '--model': 'model', '--concurrency': 'concurrency', '--max-tokens': 'maxTokens' };
    const field = fields[flag];
    if (!field) throw new Error(`unknown flag ${flag}`);
    const value = argv[++i];
    if (!value || value.startsWith('--')) throw new Error(`${flag} needs a value`);
    args[field] = ['limit', 'concurrency', 'maxTokens'].includes(field) ? Number(value) : value;
  }
  for (const field of ['limit', 'concurrency', 'maxTokens']) {
    if (field === 'limit' && args.limit === Infinity && !seen.has('--limit')) continue;
    if (!Number.isSafeInteger(args[field]) || args[field] < 1) throw new Error(`${field} must be a positive integer`);
  }
  if (args.concurrency > 16) throw new Error('--concurrency must be at most 16');
  if (args.maxTokens > 8192) throw new Error('--max-tokens must be at most 8192');
  if (!Object.hasOwn(MODELS, args.model)) throw new Error(`--model must be one of ${Object.keys(MODELS).join(', ')}`);
  return args;
}
export async function loadInputs(repo = root) {
  const dirs = (await readdir(path.join(repo, 'skills'), { withFileTypes: true })).filter(x => x.isDirectory()).map(x => x.name).sort();
  const skills = [];
  const sources = {};
  for (const file of ['eval/live.mjs', 'eval/validate-skills.mjs']) sources[file] = hash(await readFile(path.join(repo, file), 'utf8'));
  for (const dir of dirs) {
    const name = `skills/${dir}/SKILL.md`;
    const text = await readFile(path.join(repo, name), 'utf8');
    sources[name] = hash(text);
    const fields = skillMetadata(text, name);
    if (fields.name !== dir) throw new Error(`${name}: name must match directory`);
    const yamlName = `skills/${dir}/agents/openai.yaml`;
    try { sources[yamlName] = hash(await readFile(path.join(repo, yamlName), 'utf8')); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
    if (!fields.description) throw new Error(`${name} has no description`);
    skills.push({ name: fields.name ?? dir, directory: dir, description: fields.description, manualOnly: fields['disable-model-invocation'] === 'true' });
  }
  if (new Set(skills.map(s => s.name)).size !== skills.length) throw new Error('duplicate catalog skill name');
  const dir = path.join(repo, 'eval/cases');
  const files = (await readdir(dir)).filter(file => file.endsWith('.json')).sort();
  const cases = [];
  for (const file of files) {
    const text = await readFile(path.join(dir, file), 'utf8');
    sources[`eval/cases/${file}`] = hash(text);
    const items = JSON.parse(text);
    if (!Array.isArray(items)) throw new Error(`${file}: cases must be an array`);
    for (const test of items) {
      const skill = skills.find(s => s.directory === test.skill);
      if (!skill || typeof test.id !== 'string' || !test.id || typeof test.request !== 'string' || !test.request || !['required', 'forbidden', 'allowed'].includes(test.expect?.activation)) throw new Error(`${file}: invalid routing case ${test.id}`);
      cases.push({ ...test, skillName: skill.name });
    }
  }
  if (!cases.length || new Set(cases.map(t => t.id)).size !== cases.length) throw new Error('empty or duplicate case IDs');
  for (const skill of skills) for (const kind of ['positive', 'negative', 'ambiguous', 'adversarial']) {
    if (!cases.some(t => t.skill === skill.directory && t.kind === kind)) throw new Error(`${skill.name}: missing ${kind} case`);
  }
  return { skills, cases, sources };
}
export function systemPrompt(skills) {
  return ['Choose exactly one skill to load before responding, or none.', 'This is a synthetic routing probe; manual-only skills require an explicit request naming the skill.', ...skills.map(s => `- ${s.name}${s.manualOnly ? ' (manual-only)' : ''}: ${s.description}`), 'Reply with exactly one listed skill name or none. No other text.'].join('\n');
}
export function requestBody(model, system, request, maxTokens) {
  const config = MODELS[model];
  if (!config) throw new Error('unsupported model');
  if (config.provider === 'openai') return { model, instructions: system, input: request, reasoning: { effort: config.effort }, max_output_tokens: maxTokens, store: false, service_tier: 'default' };
  return { model, system, messages: [{ role: 'user', content: request }], max_tokens: maxTokens, thinking: { type: 'between_tools' }, output_config: { effort: config.effort } };
}
export function gradeRouting(test, response, names) {
  const raw = typeof response.raw === 'string' ? response.raw : '';
  const chosen = raw.trim();
  const valid = response.complete === true && (chosen === 'none' || names.has(chosen));
  let verdict = 'FAIL';
  if (valid) {
    if (test.expect.activation === 'allowed') verdict = 'INFO';
    else if (test.expect.activation === 'required' ? chosen === test.skillName : chosen !== test.skillName) verdict = 'PASS';
  }
  return { id: test.id, skill: test.skill, kind: test.kind, activation: test.expect.activation, chosen: valid ? chosen : null, valid, verdict, ...response };
}
export function summary(observations) {
  return observations.reduce((out, row) => { out[row.error ? 'error' : row.verdict.toLowerCase()]++; return out; }, { pass: 0, fail: 0, info: 0, error: 0 });
}
export function estimateCost(model, usage) {
  const price = MODELS[model];
  return ((usage.input - usage.cachedInput - (usage.cacheWrite ?? 0)) * price.input + usage.cachedInput * price.cachedInput + (usage.cacheWrite ?? 0) * price.cacheWrite + usage.output * price.output) / 1e6;
}
export async function query(model, system, request, maxTokens, fetchImpl = fetch, env = process.env) {
  const provider = MODELS[model].provider;
  const keyName = provider === 'openai' ? 'OPENAI_API_KEY' : 'ANTHROPIC_API_KEY';
  if (!env[keyName]) throw new Error(`Set ${keyName} (CLI login is not API authentication)`);
  const url = provider === 'openai' ? 'https://api.openai.com/v1/responses' : 'https://api.anthropic.com/v1/messages';
  const headers = { 'content-type': 'application/json', ...(provider === 'openai' ? { authorization: `Bearer ${env[keyName]}` } : { 'x-api-key': env[keyName], 'anthropic-version': '2023-06-01' }) };
  const response = await fetchImpl(url, { method: 'POST', headers, body: JSON.stringify(requestBody(model, system, request, maxTokens)), signal: AbortSignal.timeout(60000) });
  if (!response.ok) throw new Error(`${provider} HTTP ${response.status}`);
  const value = await response.json();
  const usage = value.usage;
  if (!usage || !Number.isSafeInteger(usage.input_tokens) || !Number.isSafeInteger(usage.output_tokens)) throw new Error('provider returned missing/invalid usage');
  const normalizedUsage = { input: usage.input_tokens, output: usage.output_tokens, cachedInput: usage.input_tokens_details?.cached_tokens ?? usage.cache_read_input_tokens ?? 0, cacheWrite: usage.input_tokens_details?.cache_write_tokens ?? usage.cache_creation_input_tokens ?? 0 };
  if (provider === 'anthropic') normalizedUsage.input += normalizedUsage.cachedInput + normalizedUsage.cacheWrite;
  if (Object.values(normalizedUsage).some(x => !Number.isSafeInteger(x) || x < 0) || normalizedUsage.cachedInput + normalizedUsage.cacheWrite > normalizedUsage.input) throw new Error('provider returned invalid usage counts');
  const messages = provider === 'openai' ? (value.output ?? []).filter(x => x.type === 'message') : [];
  const content = provider === 'openai' ? messages.flatMap(x => x.content ?? []) : value.content ?? [];
  const refused = content.some(x => x.type === 'refusal');
  const messagesComplete = provider !== 'openai' || (messages.length > 0 && messages.every(x => x.status === 'completed'));
  const raw = content.filter(x => x.type === (provider === 'openai' ? 'output_text' : 'text')).map(x => x.text).join('');
  return { rawResponse: value, rawUsage: usage, raw, complete: (provider === 'openai' ? value.status === 'completed' : value.stop_reason === 'end_turn') && value.model === model && !value.error && !refused && messagesComplete, refused, responseId: value.id, returnedModel: value.model, stopReason: value.stop_reason ?? value.status, incompleteDetails: value.incomplete_details ?? null, usage: normalizedUsage, requestId: response.headers.get('x-request-id') ?? response.headers.get('request-id') };
}
function hash(value) { return createHash('sha256').update(value).digest('hex'); }
export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const { skills, cases: allCases, sources } = await loadInputs();
  const cases = (args.case ? allCases.filter(t => t.id === args.case) : allCases).slice(0, args.limit);
  if (!cases.length) throw new Error(`no case with id ${args.case}`);
  const system = systemPrompt(skills);
  const config = MODELS[args.model];
  const startedAt = new Date().toISOString();
  const out = path.resolve(root, args.out ?? `eval/results/routing-${startedAt.replaceAll(':', '-')}.json`);
  const git = {};
  try {
    git.commit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim();
    git.status = execFileSync('git', ['status', '--short'], { cwd: root, encoding: 'utf8' }).trim();
  } catch { git.unavailable = true; }
  const metadata = { git, schemaVersion: 1, evaluation: 'synthetic-description-routing', model: args.model, provider: config.provider, startedAt, nodeVersion: process.version, settings: { maxTokens: args.maxTokens, concurrency: args.concurrency, effort: config.effort, retries: 0 }, pricing: { ...config, checkedAt: '2026-10-07', units: 'USD per million tokens', estimateOnly: true }, sources, promptHash: hash(system), prompt: system, cases, selected: cases.length, total: allCases.length, fullSelection: cases.length === allCases.length };
  if (args.dryRun) { console.log(JSON.stringify({ ...metadata, dryRun: true }, null, 2)); return 0; }
  const names = new Set(skills.map(s => s.name));
  const observations = new Array(cases.length);
  let next = 0;
  await Promise.all(Array.from({ length: Math.min(args.concurrency, cases.length) }, async () => {
    while (next < cases.length) {
      const i = next++;
      try { observations[i] = gradeRouting(cases[i], await query(args.model, system, cases[i].request, args.maxTokens), names); }
      catch (error) { observations[i] = { id: cases[i].id, skill: cases[i].skill, kind: cases[i].kind, verdict: 'FAIL', error: error.message, usage: null }; }
      console.log(`${observations[i].verdict} ${cases[i].id} (chose ${observations[i].chosen ?? 'invalid/error'})`);
    }
  }));
  const totals = summary(observations);
  const usage = observations.reduce((out, row) => { for (const key of Object.keys(out)) out[key] += row.usage?.[key] ?? 0; return out; }, { input: 0, output: 0, cachedInput: 0, cacheWrite: 0 });
  const artifact = { ...metadata, completedAt: new Date().toISOString(), summary: totals, coverage: { selected: cases.length, completed: observations.filter(row => row.complete).length, valid: observations.filter(row => row.valid).length, errors: totals.error }, usage, estimatedCostUSD: estimateCost(args.model, usage), costComplete: observations.every(row => row.usage !== null), observations };
  await mkdir(path.dirname(out), { recursive: true });
  await writeFile(out, `${JSON.stringify(artifact, null, 2)}\n`);
  console.log(`\n${totals.pass}/${totals.pass + totals.fail} scored cases passed; ${totals.info} informational; ${totals.error} API errors. ${cases.length}/${allCases.length} selected.`);
  console.log(`Estimated known usage cost $${artifact.estimatedCostUSD.toFixed(4)}${artifact.costComplete ? '' : ' (incomplete; failed requests may incur cost)'}. Evidence: ${out}`);
  return observations.some(row => row.error) ? 2 : totals.fail ? 1 : 0;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().then(code => { process.exitCode = code; }).catch(error => { console.error(`ERROR ${error.message}`); process.exitCode = 2; });
