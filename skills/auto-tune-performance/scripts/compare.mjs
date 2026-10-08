#!/usr/bin/env node
/** Compare declared independent paired performance blocks. Never runs a workload. */
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
export const EXIT_CODES = { accept: 0, reject: 1, keep_baseline: 1, invalid: 2, inconclusive: 3, needs_confirmation: 3 };
function text(value, label) {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`${label} must be a nonempty string`);
  return value;
}
function numeric(value, label, low = 0, high = Infinity, integer = false) {
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error(`${label} must be finite and numeric`);
  if (value < low || value > high || (integer && !Number.isInteger(value))) throw new Error(`${label} outside supported bounds [${low}, ${high}]`);
  return value;
}
function records(rows, label) {
  if (!Array.isArray(rows) || !rows.length) throw new Error(`${label} requires a nonempty array`);
  const seen = new Set();
  for (const row of rows) {
    if (!row || typeof row !== 'object' || Array.isArray(row)) throw new Error(`${label} entries must be objects`);
    const identity = text(row.id, `${label}.id`);
    if (seen.has(identity)) throw new Error(`duplicate ${label} id ${identity}`);
    seen.add(identity);
  }
  return rows;
}
function quantile(values, probability) {
  const position = (values.length - 1) * probability, low = Math.floor(position), high = Math.ceil(position);
  return values[low] + (values[high] - values[low]) * (position - low);
}
function mean(values) {
  // Compensated sum avoids ordinary accumulation drift in bootstrap samples.
  let sum = 0, correction = 0;
  for (const value of values) {
    const next = sum + value;
    correction += Math.abs(sum) >= Math.abs(value) ? (sum - next) + value : (value - next) + sum;
    sum = next;
  }
  return (sum + correction) / values.length;
}
const median = values => {
  const sorted = [...values].sort((a, b) => a - b), middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
};
const range = values => values.reduce(([low, high], value) => [Math.min(low, value), Math.max(high, value)], [Infinity, -Infinity]);
function effect(logRatio, direction) {
  const ratio = Math.exp(logRatio), result = 100 * (direction === 'lower' ? 1 - ratio : ratio - 1);
  if (!Number.isFinite(result)) throw new Error('non-finite calculated result');
  return result;
}
// MT19937's init_by_array and 53-bit draws match Python Random(uint32 seed).
// Only the bounded nonnegative integer seed contract is supported here.
export function randomFromSeed(seed) {
  const state = new Uint32Array(624);
  state[0] = 19650218;
  for (let i = 1; i < 624; i++) state[i] = (Math.imul(1812433253, state[i - 1] ^ (state[i - 1] >>> 30)) + i) >>> 0;
  let i = 1;
  for (let k = 624; k > 0; k--) {
    state[i] = ((state[i] ^ Math.imul(state[i - 1] ^ (state[i - 1] >>> 30), 1664525)) + seed) >>> 0;
    if (++i >= 624) { state[0] = state[623]; i = 1; }
  }
  for (let k = 623; k > 0; k--) {
    state[i] = ((state[i] ^ Math.imul(state[i - 1] ^ (state[i - 1] >>> 30), 1566083941)) - i) >>> 0;
    if (++i >= 624) { state[0] = state[623]; i = 1; }
  }
  state[0] = 0x80000000;
  let index = 624;
  function word() {
    if (index === 624) {
      for (let j = 0; j < 624; j++) {
        const y = (state[j] & 0x80000000) | (state[(j + 1) % 624] & 0x7fffffff);
        state[j] = state[(j + 397) % 624] ^ (y >>> 1) ^ ((y & 1) ? 0x9908b0df : 0);
      }
      index = 0;
    }
    let y = state[index++];
    y ^= y >>> 11; y ^= (y << 7) & 0x9d2c5680; y ^= (y << 15) & 0xefc60000; y ^= y >>> 18;
    return y >>> 0;
  }
  return () => ((word() >>> 5) * 67108864 + (word() >>> 6)) / 9007199254740992;
}
export function compare(data) {
  if (!data || Array.isArray(data) || data.version !== 1) throw new Error('expected experiment object with version 1');
  const identity = text(data.experiment_id, 'experiment_id');
  if (!['screen', 'confirm'].includes(data.phase)) throw new Error('phase must be screen or confirm');
  const design = data.design;
  if (design?.unit !== 'independent-paired-block') throw new Error('helper requires independent-paired-block design');
  const minBlocks = numeric(design.min_blocks, 'min_blocks', 4, 100000, true), confidence = numeric(design.confidence, 'confidence', .8, .999);
  const resamples = numeric(design.resamples, 'resamples', 2000, 200000, true), seed = numeric(design.seed, 'seed', 0, 2 ** 32 - 1, true);
  if (typeof design.profiled !== 'boolean') throw new Error('profiled must be boolean');
  const invalid = [], rejected = [], unknown = [];
  if (design.profiled) invalid.push('profiled outcome measurements');
  for (const arm of ['baseline', 'candidate']) for (const key of ['revision', 'environment_id', 'workload_id', 'harness_id']) text(data[arm]?.[key], `${arm}.${key}`);
  for (const key of ['environment_id', 'workload_id', 'harness_id']) if (data.baseline[key] !== data.candidate[key]) invalid.push(`arm mismatch: ${key}`);
  if (data.baseline.revision === data.candidate.revision) invalid.push('treatment identities are identical');
  const checks = records(data.hard_checks, 'hard_checks');
  for (const check of checks) {
    text(check.evidence, 'hard_check.evidence');
    for (const arm of ['baseline', 'candidate']) if (!['pass', 'fail', 'unknown'].includes(check[arm])) throw new Error('hard check must be pass, fail or unknown');
    if (check.baseline === 'fail') invalid.push(`baseline hard check failed: ${check.id}`);
    if (check.candidate === 'fail') rejected.push(`candidate hard check failed: ${check.id}`);
    if ([check.baseline, check.candidate].includes('unknown')) unknown.push(`hard check unknown: ${check.id}`);
  }
  const metrics = records(data.metrics, 'metrics');
  if (!metrics.some(metric => metric.role === 'primary')) throw new Error('at least one primary metric is required');
  for (const metric of metrics) {
    text(metric.unit, 'metric.unit');
    if (!['lower', 'higher'].includes(metric.direction) || !['primary', 'guardrail'].includes(metric.role)) throw new Error('metric requires supported direction and role');
    const threshold = numeric(metric.threshold_pct, 'threshold_pct', 0, 99.999);
    if (metric.role === 'primary' && threshold === 0) throw new Error('primary threshold_pct must be positive');
    const blocks = records(metric.blocks, 'blocks'), orders = { AB: 0, BA: 0 };
    for (const block of blocks) {
      if (!['AB', 'BA'].includes(block.order)) throw new Error('block.order must be AB or BA');
      orders[block.order]++;
      if (typeof block.valid !== 'boolean') throw new Error('block.valid must be boolean');
      if (!block.valid) invalid.push(`invalid work: ${metric.id}/${block.id}`);
      for (const arm of ['baseline', 'candidate']) { numeric(block[arm], `block.${arm}`); if (block[arm] <= 0) throw new Error('ratio analysis requires strictly positive metrics'); }
    }
    if (!orders.AB || !orders.BA || Math.abs(orders.AB - orders.BA) > 1) invalid.push(`unbalanced paired order: ${metric.id}`);
  }
  const report = { version: 1, experiment_id: identity, phase: data.phase,
    method: 'paired log-ratio percentile bootstrap with Bonferroni-adjusted bounds', family_confidence: confidence, metric_count: metrics.length,
    seed, resamples, metrics: [], hard_checks: checks,
    limitations: ['Approximate intervals assume independent comparable blocks.', 'Does not verify artifacts, manifest identities, omitted metrics or fresh confirmation.', 'Does not correct repeated peeking or candidate selection; use preplanned confirmation.'] };
  const finish = (decision, reasons) => ({ ...report, decision, reasons });
  if (invalid.length) return finish('invalid', [...invalid, ...rejected, ...unknown]);
  if (rejected.length) return finish('reject', [...rejected, ...unknown]);
  const tail = (1 - confidence) / (2 * metrics.length), resolutionOk = resamples * tail >= 10;
  for (const metric of metrics) {
    const baseline = metric.blocks.map(block => block.baseline), candidate = metric.blocks.map(block => block.candidate);
    const logs = baseline.map((b, i) => Math.log(candidate[i]) - Math.log(b));
    const row = { id: metric.id, unit: metric.unit, role: metric.role, direction: metric.direction, threshold_pct: metric.threshold_pct,
      independent_blocks: logs.length, baseline_median: median(baseline), candidate_median: median(candidate),
      baseline_range: range(baseline), candidate_range: range(candidate),
      paired_improvement_pct: effect(mean(logs), metric.direction), adjusted_interval_pct: null,
      warning: range(logs)[1] - range(logs)[0] <= 1e-12 ? 'identical paired ratios; inspect measurement resolution/duplication' : null };
    if (logs.length < minBlocks || !resolutionOk) Object.assign(row, { gate: 'inconclusive', reason: 'insufficient independent blocks or bootstrap tail resolution' });
    else {
      const random = randomFromSeed(seed), distribution = [];
      for (let j = 0; j < resamples; j++) {
        const sample = Array.from({ length: logs.length }, () => logs[Math.floor(random() * logs.length)]);
        distribution.push(mean(sample));
      }
      distribution.sort((a, b) => a - b);
      const bounds = [tail, 1 - tail].map(p => effect(quantile(distribution, p), metric.direction)).sort((a, b) => a - b);
      row.adjusted_interval_pct = bounds;
      const boundary = metric.role === 'primary' ? metric.threshold_pct : -metric.threshold_pct;
      row.gate = bounds[0] >= boundary ? 'pass' : bounds[1] < boundary ? (metric.role === 'guardrail' || bounds[1] < 0 ? 'regression' : 'no_meaningful_gain') : 'inconclusive';
    }
    report.metrics.push(row);
  }
  const gates = report.metrics.map(row => row.gate), reasons = gate => report.metrics.filter(row => row.gate === gate).map(row => `${row.id}: ${gate === 'no_meaningful_gain' ? 'gain below meaningful threshold' : gate}`);
  if (gates.includes('regression')) return finish('reject', [...reasons('regression'), ...unknown]);
  if (unknown.length || gates.includes('inconclusive')) return finish('inconclusive', [...unknown, ...reasons('inconclusive')]);
  if (gates.includes('no_meaningful_gain')) return finish('keep_baseline', reasons('no_meaningful_gain'));
  return finish(data.phase === 'confirm' ? 'accept' : 'needs_confirmation', [data.phase === 'screen' ? 'all declared gates pass; fresh confirmation required' : 'all declared confirmation gates pass']);
}
export function main(args = process.argv.slice(2)) {
  if (args.length === 1 && ['--help', '-h'].includes(args[0])) { console.log('Usage: compare.mjs EXPERIMENT.json'); return 0; }
  let report;
  try {
    if (args.length !== 1) throw new Error('expected exactly one experiment JSON path');
    report = compare(JSON.parse(fs.readFileSync(args[0], 'utf8')));
    JSON.stringify(report, (_key, value) => { if (typeof value === 'number' && !Number.isFinite(value)) throw new Error('non-finite calculated result'); return value; });
  } catch (error) { report = { decision: 'invalid', reasons: [error.message] }; }
  console.log(JSON.stringify(report, null, 2)); return EXIT_CODES[report.decision];
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) process.exitCode = main();
