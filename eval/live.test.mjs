import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { parseArgs, requestBody, gradeRouting, summary, estimateCost, query, loadInputs } from './live.mjs';
const routingCase = { id: 'unslop.test', skill: 'unslop', skillName: 'unslop', expect: { activation: 'forbidden' } };
const names = new Set(['unslop', 'remote-compute']);
test('malformed, empty, refused and truncated responses never pass negative cases', () => {
  for (const raw of ['', 'None', 'not-a-skill', 'none\nexplanation', '"none"']) {
    assert.equal(gradeRouting(routingCase, { raw, complete: true }, names).verdict, 'FAIL');
  }
  assert.equal(gradeRouting(routingCase, { raw: 'none', complete: false }, names).verdict, 'FAIL');
  assert.equal(gradeRouting(routingCase, { raw: ' none\n', complete: true }, names).verdict, 'PASS');
});
test('required, forbidden and informational grades retain their denominator', () => {
  const observe = (activation, raw) => gradeRouting({ ...routingCase, expect: { activation } }, { raw, complete: true }, names);
  assert.equal(observe('required', 'unslop').verdict, 'PASS');
  assert.equal(observe('required', 'remote-compute').verdict, 'FAIL');
  assert.equal(observe('forbidden', 'unslop').verdict, 'FAIL');
  assert.equal(observe('allowed', 'none').verdict, 'INFO');
  assert.equal(observe('allowed', 'bad').verdict, 'FAIL');
  assert.deepEqual(summary([observe('required', 'unslop'), observe('required', 'none'), observe('allowed', 'none')]), { pass: 1, fail: 1, info: 1, error: 0 });
});
test('CLI rejects zero, fractions, infinity, missing values, duplicates and unsupported models', () => {
  for (const args of [['--limit', '0'], ['--limit', '-1'], ['--limit', '1.5'], ['--limit', 'Infinity'], ['--model', 'claude-haiku-4-5'], ['--model', 'gpt-6-pro'], ['--case'], ['--out', '--limit'], ['--limit', '1', '--limit', '2'], ['--concurrency', '17'], ['--max-tokens', '9000']]) assert.throws(() => parseArgs(args));
  assert.equal(parseArgs([]).model, 'gpt-6.1-sol');
  assert.equal(parseArgs(['--dry-run', '--model', 'gpt-6-luna', '--limit', '2']).limit, 2);
});
test('provider requests use supported thinking params and avoid persistence/temperature', () => {
  const sol = requestBody('gpt-6.1-sol', 'system', 'request', 512);
  assert.equal(sol.store, false);
  assert.equal(sol.reasoning.effort, 'low');
  assert.equal(sol.max_output_tokens, 512);
  assert.equal(sol.temperature, undefined);
  const sonnet = requestBody('claude-sonnet-5-5', 'system', 'request', 512);
  assert.deepEqual(sonnet.thinking, { type: 'between_tools' });
  assert.equal(sonnet.temperature, undefined);
  assert.throws(() => requestBody('gpt-6-pro', '', '', 10));
});
test('cost accounting uses selected model and cache rates', () => {
  const usage = { input: 1000000, cachedInput: 100000, output: 100000 };
  assert.equal(estimateCost('gpt-6.1-sol', usage), 2.81);
  assert.equal(estimateCost('gpt-6-luna', usage), 0.141);
});
test('OpenAI adapter preserves status and usage; incomplete text remains incomplete', async () => {
  let sent;
  const response = { id: 'resp-test', model: 'gpt-6.1-sol', status: 'incomplete', incomplete_details: { reason: 'max_output_tokens' }, usage: { input_tokens: 12, output_tokens: 8, input_tokens_details: { cached_tokens: 2 } }, output: [{ type: 'message', content: [{ type: 'output_text', text: 'none' }] }] };
  const mock = async (url, args) => { sent = { url, body: JSON.parse(args.body) }; return { ok: true, json: async () => response, headers: new Headers({ 'x-request-id': 'req-test' }) }; };
  const result = await query('gpt-6.1-sol', 'system', 'request', 512, mock, { OPENAI_API_KEY: 'test' });
  assert.equal(sent.url, 'https://api.openai.com/v1/responses');
  assert.equal(sent.body.store, false);
  assert.equal(result.complete, false);
  assert.equal(result.raw, 'none');
  assert.deepEqual(result.usage, { input: 12, output: 8, cachedInput: 2, cacheWrite: 0 });
  assert.equal(result.requestId, 'req-test');
});
test('Sonnet adapter handles refusal without silently converting it to none', async () => {
  const mock = async () => ({ ok: true, json: async () => ({ id: 'msg-test', model: 'claude-sonnet-5-5', stop_reason: 'refusal', content: [{ type: 'text', text: 'none' }], usage: { input_tokens: 4, output_tokens: 2 } }), headers: new Headers() });
  const response = await query('claude-sonnet-5-5', '', '', 512, mock, { ANTHROPIC_API_KEY: 'test' });
  assert.equal(gradeRouting(routingCase, response, names).verdict, 'FAIL');
});
test('HTTP and absent usage fail visibly; credential absence makes no call', async () => {
  let called = false;
  const mock = async () => { called = true; return { ok: false, status: 401 }; };
  await assert.rejects(query('gpt-6.1-sol', '', '', 512, mock, {}), /OPENAI_API_KEY/);
  assert.equal(called, false);
  await assert.rejects(query('gpt-6.1-sol', '', '', 512, mock, { OPENAI_API_KEY: 'test' }), /HTTP 401/);
  await assert.rejects(query('gpt-6.1-sol', '', '', 512, async () => ({ ok: true, json: async () => ({}) }), { OPENAI_API_KEY: 'test' }), /usage/);
});
test('repository catalog and all cases have coverage and content hashes', async () => {
  const { cases, sources } = await loadInputs();
  assert.ok(cases.length >= 24);
  assert.ok(Object.keys(sources).some(x => x.startsWith('skills/')));
  assert.ok(Object.keys(sources).some(x => x.startsWith('eval/cases/')));
  assert.ok(Object.values(sources).every(x => /^[0-9a-f]{64}$/.test(x)));
});

test('Anthropic cache usage is normalized and priced separately', async () => {
  const mock = async () => ({ ok: true, json: async () => ({ model: 'claude-sonnet-5-5', stop_reason: 'end_turn', content: [{ type: 'text', text: 'none' }], usage: { input_tokens: 10, output_tokens: 2, cache_read_input_tokens: 100, cache_creation_input_tokens: 20 } }), headers: new Headers() });
  const result = await query('claude-sonnet-5-5', '', '', 512, mock, { ANTHROPIC_API_KEY: 'test' });
  assert.deepEqual(result.usage, { input: 130, output: 2, cachedInput: 100, cacheWrite: 20 });
  assert.equal(estimateCost('claude-sonnet-5-5', result.usage), 0.0001);
  assert.equal(result.rawResponse.stop_reason, 'end_turn');
});
test('transport errors are separate from scored case failures', () => {
  assert.deepEqual(summary([{ verdict: 'FAIL', error: 'HTTP 429' }, { verdict: 'FAIL' }]), { pass: 0, fail: 1, info: 0, error: 1 });
});

test('refusal, provider errors and incomplete messages cannot pass with valid-looking text', async () => {
  const envelope = (content, status = 'completed', error = null) => ({
    model: 'gpt-6.1-sol', status: 'completed', error,
    usage: { input_tokens: 10, output_tokens: 2 },
    output: [{ type: 'message', status, content }],
  });
  const text = { type: 'output_text', text: 'none' };
  for (const value of [
    envelope([{ type: 'refusal', refusal: 'declined' }, text]),
    envelope([text], 'incomplete'),
    envelope([text], 'completed', { message: 'provider error' }),
  ]) {
    const mock = async () => ({ ok: true, json: async () => value, headers: new Headers() });
    const response = await query('gpt-6.1-sol', '', '', 512, mock, { OPENAI_API_KEY: 'test' });
    assert.equal(response.raw, 'none');
    assert.equal(response.complete, false);
    assert.equal(gradeRouting(routingCase, response, names).verdict, 'FAIL');
    assert.deepEqual(response.rawResponse, value);
  }
});

test('completed OpenAI response passes through the adapter to strict grading', async () => {
  const value = { model: 'gpt-6.1-sol', status: 'completed', usage: { input_tokens: 10, output_tokens: 2 },
    output: [{ type: 'message', status: 'completed', content: [{ type: 'output_text', text: 'none' }] }] };
  const mock = async () => ({ ok: true, json: async () => value, headers: new Headers() });
  const response = await query('gpt-6.1-sol', '', '', 512, mock, { OPENAI_API_KEY: 'test' });
  assert.equal(gradeRouting(routingCase, response, names).verdict, 'PASS');
});

test('public CLI retains partial API errors as reviewable evidence without credentials', async () => {
  const dir = await mkdtemp(path.join(tmpdir(), 'ai-skillz-live-'));
  try {
    const file = path.join(dir, 'failed.json');
    const child = spawnSync(process.execPath, [new URL('./live.mjs', import.meta.url).pathname, '--limit', '2', '--out', file], { encoding: 'utf8', env: { ...process.env, OPENAI_API_KEY: '', ANTHROPIC_API_KEY: '' } });
    assert.equal(child.status, 2);
    const artifact = JSON.parse(await readFile(file, 'utf8'));
    assert.equal(artifact.fullSelection, false);
    assert.equal(artifact.summary.error, 2);
    assert.equal(artifact.summary.pass, 0);
    assert.equal(artifact.costComplete, false);
    assert.equal(artifact.observations.length, 2);
    assert.equal(artifact.observations[0].error, 'Set OPENAI_API_KEY (CLI login is not API authentication)');
    assert.match(artifact.promptHash, /^[0-9a-f]{64}$/);
  } finally { await rm(dir, { recursive: true, force: true }); }
});
