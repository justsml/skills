import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { setup, status, estimate, jsonOutput } from './remote_compute.mjs';
const dir = path.dirname(fileURLToPath(import.meta.url));
const now = Date.parse('2026-10-07T12:00:00Z');
function resource(id = 'live', run = 'run-a', low = .5, high = .8, ended = false) {
  return { id, provider: 'gpu', run_id: run, owned: true, billing_ended: ended, rate_low_usd: low, rate_high_usd: high, active_jobs: 0, pending_jobs: 0 };
}
function fixture() {
  const project = fs.mkdtempSync(path.join(os.tmpdir(), 'remote-parity-'));
  setup(project); const base = path.join(project, '.remote-compute');
  const config = JSON.parse(fs.readFileSync(path.join(base, 'config.json')));
  config.providers = [{ alias: 'gpu' }]; Object.assign(config.budget, { hourly_usd: 1, run_usd: 10, cleanup_reserve_usd: 1 });
  const snapshot = { version: 1, observed_at: '2026-10-07T12:00:00Z', coverage: 'complete', providers: [{ alias: 'gpu', inventory_status: 'verified', billing_status: 'unknown' }],
    resources: [resource(), resource('old', 'run-a', null, null, true)],
    runs: [{ id: 'run-a', thread_id: 'thread-a', measured_usd: 2, estimated_usd: 1, committed_usd: .5, unknown_cost: false, eta_hours_low: 1, eta_hours_high: 5 }] };
  return { project, base, config, snapshot, save() {
    fs.writeFileSync(path.join(base, 'config.json'), JSON.stringify(config)); fs.writeFileSync(path.join(base, 'state/snapshot.json'), JSON.stringify(snapshot));
  }, cleanup() { fs.rmSync(project, { recursive: true, force: true }); } };
}
test('setup preserves policy, snapshots and refuses redirected state', () => {
  const f = fixture();
  try {
    f.save(); const before = fs.readFileSync(path.join(f.base, 'config.json'), 'utf8');
    assert.deepEqual(setup(f.project).created, []); assert.equal(fs.readFileSync(path.join(f.base, 'config.json'), 'utf8'), before);
    assert.equal(f.config.authorization.paid_compute, false);
    fs.rmSync(path.join(f.base, 'state'), { recursive: true }); fs.symlinkSync(f.project, path.join(f.base, 'state'), 'dir');
    assert.throws(() => setup(f.project), /symlink/);
  } finally { f.cleanup(); }
});
const variants = [
  [f => {}, null],
  [f => { f.snapshot.resources[0].rate_high_usd = null; }, null],
  [f => { f.snapshot.observed_at = '2026-10-07T10:00:00Z'; }, null],
  [f => { f.config.providers.push({ alias: 'other' }); }, null],
  [f => { f.snapshot.runs[0].unknown_cost = true; }, null],
  [f => { f.snapshot.resources[0].state = 'stopped'; }, null],
  [f => { f.config.budget.run_usd = 0; }, null],
  [f => {
    f.snapshot.runs.push({ ...f.snapshot.runs[0], id: 'run-b' }); f.snapshot.resources.push(resource('peer', 'run-b', 2, 3));
    f.snapshot.resources.push({ ...resource('borrowed', 'run-a', 99, 99), owned: false });
  }, 'run-a'],
];
test('accounting retains accrual, stopped charges, unknowns and aggregate scope', () => {
  for (const [mutate, run] of variants) {
    const f = fixture();
    try {
      mutate(f); f.save(); const report = status(f.project, run, now);
      if (report.complete_forecast) assert.ok(report.aggregate_rate_usd_per_hour);
      else { assert.equal(report.aggregate_rate_usd_per_hour, null); assert.equal(report.runs[0].final_flat_fleet_usd, null); }
      if (run) { assert.ok(report.warnings.includes('aggregate project rate exceeds hourly ceiling')); assert.equal(report.resources.length, 2); }
    } finally { f.cleanup(); }
  }
  const f = fixture(); try { f.save(); assert.deepEqual(status(f.project, null, now).runs[0].final_flat_fleet_usd, [4, 7.5]); } finally { f.cleanup(); }
});
test('invalid ownership, budgets, timestamps and overflow fail clearly', () => {
  const mutations = [f => { f.snapshot.resources.push(resource()); }, f => { f.snapshot.resources[0].run_id = 'missing'; },
    f => { f.config.budget.hourly_usd = true; }, f => { f.config.budget.hourly_usd = -1; },
    f => { f.snapshot.observed_at = '2026-10-07T12:00:00'; }, f => { f.snapshot.observed_at = '2026-10-08T12:00:00Z'; }, f => { f.snapshot.observed_at = '2026-02-30T12:00:00Z'; }];
  for (const mutate of mutations) { const f = fixture(); try { mutate(f); f.save(); assert.throws(() => status(f.project, null, now)); } finally { f.cleanup(); } }
  assert.throws(() => jsonOutput(estimate(1e308, 1e308, 24, 24)), /non-finite/);
  assert.throws(() => estimate(2, 1, 1, 5));
});
const hasPython = spawnSync('python3', ['-c', 'import sys; sys.exit(sys.version_info < (3,10))']).status === 0;
test('Python and Node saved reports and estimates agree', { skip: !hasPython }, () => {
  for (const [mutate, run] of variants) {
    const f = fixture(); try {
      mutate(f); f.save();
      const code = 'import sys,importlib.util,json; from pathlib import Path; from datetime import datetime,timezone; s=importlib.util.spec_from_file_location("helper",sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(json.dumps(m.status(Path(sys.argv[2]),sys.argv[3] or None,datetime(2026,10,7,12,tzinfo=timezone.utc))))';
      const proc = spawnSync('python3', ['-c', code, path.join(dir, 'remote_compute.py'), f.project, run ?? ''], { encoding: 'utf8' });
      assert.equal(proc.status, 0, proc.stderr); assert.deepEqual(status(f.project, run, now), JSON.parse(proc.stdout));
    } finally { f.cleanup(); }
  }
  const args = ['estimate', '--rate-low', '.5', '--rate-high', '.8', '--hours-low', '1', '--hours-high', '5', '--fixed', '.2'];
  const p = spawnSync('python3', [path.join(dir, 'remote_compute.py'), ...args], { encoding: 'utf8' });
  assert.deepEqual(estimate(.5, .8, 1, 5, .2), JSON.parse(p.stdout));
});
test('Node/Bash CLI handles paths with spaces, estimates, argument errors and idempotence', () => {
  const project = fs.mkdtempSync(path.join(os.tmpdir(), 'remote with spaces-'));
  try {
    for (const [runtime, script] of [[process.execPath, 'remote_compute.mjs'], ['bash', 'remote_compute.sh']]) {
      const call = args => spawnSync(runtime, [path.join(dir, script), ...args], { encoding: 'utf8' });
      let proc = call(['setup', '--project', project]); assert.equal(proc.status, 0, proc.stderr);
      proc = call(['setup', '--project', project]); assert.deepEqual(JSON.parse(proc.stdout).created, []);
      proc = call(['status', '--project', project]); assert.equal(proc.status, 0); assert.equal(JSON.parse(proc.stdout).complete_forecast, false);
      proc = call(['estimate', '--rate-low', '.5', '--rate-high', '.8', '--hours-low', '1', '--hours-high', '5']); assert.equal(proc.status, 0); assert.deepEqual(JSON.parse(proc.stdout).workload_usd, [.5, 4]);
      for (const args of [[], ['status'], ['estimate', '--wat', '1'], ['estimate', '--rate-low', '0x10', '--rate-high', '20', '--hours-low', '1', '--hours-high', '1'], ['estimate', '--rate-low', ' ', '--rate-high', '20', '--hours-low', '1', '--hours-high', '1']]) assert.equal(call(args).status, 2);
    }
  } finally { fs.rmSync(project, { recursive: true, force: true }); }
});
test('ceilings use unrounded forecasts, missing budgets fail, unknown project rates warn', () => {
  const f = fixture();
  try {
    f.config.budget.cleanup_reserve_usd = 0; f.config.budget.run_usd = 7.5;
    f.snapshot.resources[0].rate_high_usd = .80000001; f.save();
    const report = status(f.project, null, now);
    assert.equal(report.runs[0].final_flat_fleet_usd[1], 7.5);
    assert.ok(report.warnings.includes('run run-a forecast plus cleanup reserve exceeds run ceiling'));
    f.snapshot.resources[0].rate_high_usd = null; f.save();
    assert.ok(status(f.project, null, now).warnings.includes('hourly ceiling cannot be assessed: project rates are unknown'));
    delete f.config.budget.hourly_usd; f.save(); assert.throws(() => status(f.project, null, now), /missing budget/);
  } finally { f.cleanup(); }
});
test('Bash selects Python without Node, fails without either, never retries validation failure', { skip: !hasPython }, () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'runtime selection-'));
  try {
    const executable = name => spawnSync('/bin/sh', ['-c', 'command -v "$1"', 'sh', name], { encoding: 'utf8' }).stdout.trim();
    fs.symlinkSync(executable('dirname'), path.join(temp, 'dirname'));
    fs.symlinkSync(executable('python3'), path.join(temp, 'python3'));
    const call = () => spawnSync('/bin/bash', [path.join(dir, 'remote_compute.sh'), 'estimate', '--rate-low', '1', '--rate-high', '1', '--hours-low', '1', '--hours-high', '1'], { env: { ...process.env, PATH: temp }, encoding: 'utf8' });
    let proc = call(); assert.equal(proc.status, 0, proc.stderr); assert.deepEqual(JSON.parse(proc.stdout).workload_usd, [1, 1]);
    fs.unlinkSync(path.join(temp, 'python3')); proc = call(); assert.equal(proc.status, 2); assert.match(proc.stderr, /neither compatible runtime/);
    fs.symlinkSync(executable('python3'), path.join(temp, 'python3'));
    fs.writeFileSync(path.join(temp, 'node'), '#!/bin/sh\nif [ "$1" = "-e" ]; then exit 0; fi\nprintf "selected-helper-rejection\\n" >&2\nexit 2\n', { mode: 0o700 });
    proc = call(); assert.equal(proc.status, 2); assert.equal(proc.stdout, ''); assert.match(proc.stderr, /selected-helper-rejection/);
  } finally { fs.rmSync(temp, { recursive: true, force: true }); }
});
