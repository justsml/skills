import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { compare, randomFromSeed } from './compare.mjs';
const dir = path.dirname(fileURLToPath(import.meta.url));
function metric(ratios = [.79, .81, .80, .82, .78, .80, .81, .79]) {
  return { id: 'latency', unit: 'ms', role: 'primary', direction: 'lower', threshold_pct: 5,
    blocks: ratios.map((ratio, i) => ({ id: `b${i}`, order: i % 2 ? 'BA' : 'AB', valid: true, baseline: 100 + i, candidate: (100 + i) * ratio })) };
}
function experiment() {
  return { version: 1, experiment_id: 'synthetic', phase: 'confirm',
    baseline: { revision: 'base', environment_id: 'env', workload_id: 'work', harness_id: 'harness' },
    candidate: { revision: 'candidate', environment_id: 'env', workload_id: 'work', harness_id: 'harness' },
    design: { unit: 'independent-paired-block', min_blocks: 8, confidence: .95, resamples: 2000, seed: 42, profiled: false },
    hard_checks: [{ id: 'output', baseline: 'pass', candidate: 'pass', evidence: 'oracle.json' }], metrics: [metric()] };
}
const variants = [
  ['accept', () => {}], ['needs_confirmation', d => { d.phase = 'screen'; }],
  ['accept', d => { d.metrics = [metric(Array(8).fill(1.25))]; d.metrics[0].direction = 'higher'; }],
  ['reject', d => { d.metrics.push({ ...metric(Array(8).fill(1.3)), id: 'memory', role: 'guardrail', threshold_pct: 2 }); }],
  ['keep_baseline', d => { d.metrics = [metric(Array(8).fill(.98))]; }],
  ['inconclusive', d => { d.metrics = [metric([.5, 1.5, .5, 1.5, .5, 1.5, .5, 1.5])]; }],
  ['inconclusive', d => { d.metrics = [metric(Array(4).fill(.8))]; }],
  ['invalid', d => { d.metrics[0].blocks[0].valid = false; }],
  ['invalid', d => { d.candidate.environment_id = 'different'; }],
  ['invalid', d => { d.design.profiled = true; }],
  ['invalid', d => { d.metrics[0].blocks.forEach(b => { b.order = 'AB'; }); }],
  ['reject', d => { d.hard_checks[0].candidate = 'fail'; }],
  ['inconclusive', d => { d.hard_checks[0].candidate = 'unknown'; }],
  ['invalid', d => { d.hard_checks[0].baseline = 'fail'; }],
];
test('correctness, guardrails, uncertainty and screening decisions', () => {
  for (const [expected, mutate] of variants) { const data = experiment(); mutate(data); assert.equal(compare(data).decision, expected); }
});
test('rejects invalid numbers, duplicated observations and unsupported declarations', () => {
  for (const value of [0, -1, NaN, Infinity, true]) { const d = experiment(); d.metrics[0].blocks[0].candidate = value; assert.throws(() => compare(d)); }
  const d = experiment(); d.metrics[0].blocks[1].id = 'b0'; assert.throws(() => compare(d), /duplicate/);
  d.version = true; assert.throws(() => compare(d));
});
test('family adjustment widens intervals and draws reproduce Python known values', () => {
  const d = experiment(), first = compare(d);
  d.metrics.push({ ...metric(), id: 'memory', role: 'guardrail', threshold_pct: 2 });
  const second = compare(d), [a, b] = first.metrics[0].adjusted_interval_pct, [c, e] = second.metrics[0].adjusted_interval_pct;
  assert.ok(c <= a && e >= b); assert.deepEqual(compare(d), second);
  const rng = randomFromSeed(42); assert.equal(rng(), 0.6394267984578837); assert.equal(rng(), 0.025010755222666936);
});
function close(actual, expected) {
  if (typeof expected === 'number') { assert.ok(Math.abs(actual - expected) <= 1e-10 * Math.max(1, Math.abs(expected)), `${actual} != ${expected}`); return; }
  if (Array.isArray(expected)) { assert.equal(actual.length, expected.length); expected.forEach((v, i) => close(actual[i], v)); return; }
  if (expected && typeof expected === 'object') { assert.deepEqual(Object.keys(actual).sort(), Object.keys(expected).sort()); for (const key of Object.keys(expected)) close(actual[key], expected[key]); return; }
  assert.equal(actual, expected);
}
const hasPython = spawnSync('python3', ['-c', 'import sys; sys.exit(sys.version_info < (3,10))']).status === 0;
test('Python/Node reports agree across decision paths, metrics and seeds', { skip: !hasPython }, () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'compare-parity-'));
  try {
    const file = path.join(temp, 'experiment.json');
    for (const seed of [0, 42, 4294967295]) for (const [, mutate] of variants) {
      const d = experiment(); mutate(d); d.design.seed = seed; fs.writeFileSync(file, JSON.stringify(d));
      const python = spawnSync('python3', [path.join(dir, 'compare.py'), file], { encoding: 'utf8' });
      close(compare(d), JSON.parse(python.stdout));
    }
  } finally { fs.rmSync(temp, { recursive: true, force: true }); }
});
test('Node and Bash preserve decision exit codes and malformed JSON reports', () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'compare-cli-'));
  try {
    const file = path.join(temp, 'data.json');
    for (const [runtime, script] of [[process.execPath, 'compare.mjs'], ['bash', 'compare.sh']]) {
      for (const [expected, mutate] of variants) {
        const d = experiment(); mutate(d); fs.writeFileSync(file, JSON.stringify(d));
        const proc = spawnSync(runtime, [path.join(dir, script), file], { encoding: 'utf8' });
        assert.equal(JSON.parse(proc.stdout).decision, expected);
        assert.equal(proc.status, { accept: 0, reject: 1, keep_baseline: 1, invalid: 2, inconclusive: 3, needs_confirmation: 3 }[expected]);
      }
      fs.writeFileSync(file, '{'); const proc = spawnSync(runtime, [path.join(dir, script), file], { encoding: 'utf8' });
      assert.equal(proc.status, 2); assert.equal(JSON.parse(proc.stdout).decision, 'invalid');
    }
  } finally { fs.rmSync(temp, { recursive: true, force: true }); }
});
