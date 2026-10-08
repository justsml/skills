#!/usr/bin/env node
/** Local scaffolding and flat-fleet forecasts. No network, secrets or cloud mutations. */
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

function number(value, label, nullable = false) {
  if (nullable && value == null) return null;
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) throw new Error(`${label} must be a finite nonnegative number`);
  return value;
}
function instant(value) {
  const match = typeof value === 'string' && /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(Z|[+-]\d{2}:\d{2})$/.exec(value);
  if (!match) throw new Error('timestamp must be an ISO 8601 string with timezone');
  const [, y, m, d, h, min, sec, zone] = match;
  const year = Number(y), month = Number(m), day = Number(d);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > days[month - 1] || Number(h) > 23 || Number(min) > 59 || Number(sec) > 59 || (zone !== 'Z' && (Number(zone.slice(1, 3)) > 23 || Number(zone.slice(4)) > 59)) || !Number.isFinite(Date.parse(value))) throw new Error('invalid ISO 8601 timestamp');
  return Date.parse(value);
}
function load(file) {
  const data = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (!data || Array.isArray(data) || data.version !== 1) throw new Error(`${path.basename(file)}: expected object with version 1`);
  return data;
}
function uniqueRows(rows, field, label) {
  if (!Array.isArray(rows)) throw new Error(`${label} must be an array`);
  const seen = new Set();
  for (const row of rows) {
    if (!row || typeof row[field] !== 'string' || !row[field]) throw new Error(`${label}: missing ${field}`);
    if (seen.has(row[field])) throw new Error(`${label}: duplicate ${field}`);
    seen.add(row[field]);
  }
  return seen;
}
const rounded = value => value == null ? null : Number(value.toPrecision(6));
const sum = values => values.reduce((a, b) => a + b, 0);
function scenarios(low, high, fixed = 0) {
  return { extra_1_to_5h_usd: low == null || high == null ? null : [rounded(low + fixed), rounded(5 * high + fixed)],
    unchanged_24h_usd: low == null || high == null ? null : [rounded(24 * low + fixed), rounded(24 * high + fixed)] };
}
function createMissing(file, content) {
  let fd;
  try { fd = fs.openSync(file, 'wx', 0o600); }
  catch (error) { if (error.code === 'EEXIST') return false; throw error; }
  try { fs.writeFileSync(fd, content); } finally { fs.closeSync(fd); }
  return true;
}
export function setup(project) {
  if (!fs.statSync(project).isDirectory()) throw new Error('--project must identify an existing workspace directory');
  project = fs.realpathSync(project);
  const base = path.join(project, '.remote-compute');
  for (const directory of [base, path.join(base, 'state')]) {
    try { if (fs.lstatSync(directory).isSymbolicLink()) throw new Error('configuration/state directory must not be a symlink'); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
    try { fs.mkdirSync(directory, { mode: 0o700 }); } catch (error) { if (error.code !== 'EEXIST' || !fs.statSync(directory).isDirectory()) throw error; }
  }
  const config = { version: 1, project_id: path.basename(project), currency: 'USD',
    budget: { hourly_usd: null, rolling_24h_usd: null, run_usd: null, cleanup_reserve_usd: 0 },
    authorization: { paid_compute: false, source: null, scope: null, expires_at: null },
    constraints: { regions: [], data_residency: null, allowed_data: [], max_workers: 1, max_runtime_hours: null, spot_allowed: false, gpu: null },
    providers: [], monitoring: { checkpoint_seconds: 600, stale_after_seconds: 600 } };
  const snapshot = { version: 1, observed_at: null, coverage: 'unknown', providers: [], resources: [], runs: [] };
  const files = [
    ['config.json', JSON.stringify(config, null, 2) + '\n'],
    ['.gitignore', 'state/\nsecrets.env\nsecrets.env.*\n!secrets.env.example\n*.key\n*.pem\n'],
    ['secrets.env.example', "# Names only. Add only the selected provider's bindings.\n# RUNPOD_API_KEY=\n# VAST_API_KEY=\n# LAMBDA_API_KEY=\n"],
    ['state/snapshot.json', JSON.stringify(snapshot, null, 2) + '\n'] ];
  const created = [], preserved = [];
  for (const [name, content] of files) {
    const file = path.join(base, name);
    (createMissing(file, content) ? created : preserved).push(file);
  }
  return { created, preserved, next: 'Choose providers, constraints and budget; record authorization and verify access/cleanup before renting.' };
}
export function status(project, runId = null, now = Date.now()) {
  const base = path.join(project, '.remote-compute');
  const config = load(path.join(base, 'config.json')), snapshot = load(path.join(base, 'state/snapshot.json'));
  if (config.currency !== 'USD') throw new Error('helper supports USD only; convert native currency explicitly');
  const budget = config.budget;
  for (const key of ['hourly_usd', 'rolling_24h_usd', 'run_usd', 'cleanup_reserve_usd']) {
    if (!Object.hasOwn(budget, key)) throw new Error(`missing budget.${key}; use explicit null for unspecified ceilings`);
    number(budget[key], `budget.${key}`, key !== 'cleanup_reserve_usd');
  }
  const aliases = uniqueRows(config.providers, 'alias', 'config.providers'), observed = uniqueRows(snapshot.providers, 'alias', 'snapshot.providers');
  if ([...observed].some(alias => !aliases.has(alias))) throw new Error('snapshot contains an unconfigured provider alias');
  uniqueRows(snapshot.runs, 'id', 'runs');
  if (!Array.isArray(snapshot.resources)) throw new Error('resources must be an array');
  const resourceKeys = new Set();
  for (const resource of snapshot.resources) {
    if (!resource) throw new Error('resource must be an object');
    const key = JSON.stringify([resource.provider, resource.id]);
    if (![resource.provider, resource.id].every(v => typeof v === 'string' && v) || !aliases.has(resource.provider) || resourceKeys.has(key)) throw new Error('resource requires a configured provider and unique provider/id pair');
    resourceKeys.add(key);
    for (const field of ['owned', 'billing_ended']) if (typeof resource[field] !== 'boolean') throw new Error(`resource.${field} must be boolean`);
    const low = number(resource.rate_low_usd, 'rate_low_usd', true), high = number(resource.rate_high_usd, 'rate_high_usd', true);
    if (low != null && high != null && low > high) throw new Error('rate_low_usd exceeds rate_high_usd');
    for (const field of ['active_jobs', 'pending_jobs']) {
      const count = number(resource[field], field, true);
      if (count != null && !Number.isInteger(count)) throw new Error(`${field} must be an integer or null`);
    }
  }
  const threshold = number(config.monitoring.stale_after_seconds, 'stale_after_seconds');
  const age = snapshot.observed_at == null ? null : (now - instant(snapshot.observed_at)) / 1000;
  if (age != null && age < -60) throw new Error('snapshot timestamp is in the future');
  const stale = age == null || age > threshold, reasons = [];
  const missing = [...aliases].filter(alias => !observed.has(alias)).sort();
  if (stale) reasons.push('missing or stale observations');
  if (missing.length) reasons.push('configured providers missing from snapshot: ' + missing.join(', '));
  if (!['complete', 'partial', 'unknown'].includes(snapshot.coverage)) throw new Error('invalid coverage');
  if (snapshot.coverage !== 'complete') reasons.push('inventory/cost coverage is incomplete');
  const fields = (row, keys) => Object.fromEntries(keys.map(key => [key, row[key] ?? null]));
  const providers = snapshot.providers.map(provider => {
    for (const field of ['inventory_status', 'billing_status']) if (!['verified', 'unknown', 'invalid-auth', 'dashboard-only'].includes(provider[field])) throw new Error(`invalid provider.${field}`);
    for (const field of ['balance_usd', 'recent_usage_usd']) if (provider[field] != null && (typeof provider[field] !== 'number' || !Number.isFinite(provider[field]))) throw new Error(`${field} must be finite or null`);
    if (provider.inventory_status !== 'verified') reasons.push(`inventory not verified for ${provider.alias}`);
    return fields(provider, ['alias', 'inventory_status', 'billing_status', 'balance_usd', 'recent_usage_usd', 'usage_window', 'source']);
  });
  const runs = snapshot.runs, knownRunIds = new Set(runs.map(run => run.id));
  for (const resource of snapshot.resources) if (resource.owned && !knownRunIds.has(resource.run_id)) throw new Error('owned resource requires a recorded run_id');
  if (runId != null && !knownRunIds.has(runId)) throw new Error('requested run is not recorded');
  for (const run of runs) {
    for (const field of ['measured_usd', 'estimated_usd', 'committed_usd', 'eta_hours_low', 'eta_hours_high']) number(run[field], `run.${field}`, field.startsWith('eta_'));
    if (typeof run.unknown_cost !== 'boolean') throw new Error('run.unknown_cost must be boolean');
    if (run.eta_hours_low != null && run.eta_hours_high != null && run.eta_hours_low > run.eta_hours_high) throw new Error('ETA low exceeds ETA high');
  }
  const selected = runs.filter(run => runId == null || run.id === runId);
  const resources = snapshot.resources.filter(r => r.owned && (runId == null || r.run_id === runId)), live = resources.filter(r => !r.billing_ended);
  if (live.some(r => r.rate_low_usd == null || r.rate_high_usd == null)) reasons.push('billable resources have unknown rates');
  if (selected.some(run => run.unknown_cost)) reasons.push('selected runs have unknown costs');
  const low = sum(live.map(r => r.rate_low_usd ?? 0)), high = sum(live.map(r => r.rate_high_usd ?? 0)), complete = reasons.length === 0;
  const totals = Object.fromEntries(['measured_usd', 'estimated_usd', 'committed_usd'].map(field => [field, rounded(sum(selected.map(run => run[field])))]));
  const finalHighRaw = new Map();
  const forecasts = selected.map(run => {
    const runLive = live.filter(r => r.run_id === run.id);
    let final = null;
    if (complete && run.eta_hours_low != null && run.eta_hours_high != null) {
      const accrued = sum(Object.keys(totals).map(field => run[field]));
      finalHighRaw.set(run.id, accrued + sum(runLive.map(r => r.rate_high_usd)) * run.eta_hours_high);
      final = [rounded(accrued + sum(runLive.map(r => r.rate_low_usd)) * run.eta_hours_low), rounded(accrued + sum(runLive.map(r => r.rate_high_usd)) * run.eta_hours_high)];
    }
    return { id: run.id, thread_id: run.thread_id ?? null, final_flat_fleet_usd: final };
  });
  const warnings = [], projectLive = snapshot.resources.filter(r => r.owned && !r.billing_ended);
  const projectHigh = projectLive.some(r => r.rate_high_usd == null) ? null : sum(projectLive.map(r => r.rate_high_usd));
  if (budget.hourly_usd != null && projectHigh == null) warnings.push('hourly ceiling cannot be assessed: project rates are unknown');
  if (budget.hourly_usd != null && projectHigh != null && projectHigh > budget.hourly_usd) warnings.push('aggregate project rate exceeds hourly ceiling');
  for (const forecast of forecasts) if (budget.run_usd != null && forecast.final_flat_fleet_usd != null && finalHighRaw.get(forecast.id) + budget.cleanup_reserve_usd > budget.run_usd) warnings.push(`run ${forecast.id} forecast plus cleanup reserve exceeds run ceiling`);
  return { mode: 'saved-observations-only', observed_at: snapshot.observed_at ?? null, stale, scope: runId || 'project', providers,
    missing_provider_aliases: missing, resources: resources.map(r => fields(r, ['id', 'provider', 'run_id', 'kind', 'state', 'billing_ended', 'active_jobs', 'pending_jobs'])),
    budget, known_accrual_usd: totals, complete_forecast: complete, incomplete_reasons: reasons, known_rate_subtotal_usd_per_hour: [rounded(low), rounded(high)],
    aggregate_rate_usd_per_hour: complete ? [rounded(low), rounded(high)] : null, ...scenarios(complete ? low : null, complete ? high : null), runs: forecasts,
    warnings, enforcement: 'none; rolling-24h, authorization and deadlines require the project supervisor', exclusions: 'Flat fleet only; incremental non-hourly charges must be included separately.' };
}
export function estimate(rateLow, rateHigh, hoursLow, hoursHigh, fixed = 0) {
  for (const [label, value] of Object.entries({ rate_low: rateLow, rate_high: rateHigh, hours_low: hoursLow, hours_high: hoursHigh, fixed })) number(value, label);
  if (rateLow > rateHigh || hoursLow > hoursHigh) throw new Error('low bounds must not exceed high bounds');
  return { mode: 'planning-estimate-only', currency: 'USD', workload_usd: [rounded(rateLow * hoursLow + fixed), rounded(rateHigh * hoursHigh + fixed)], ...scenarios(rateLow, rateHigh, fixed), assumption: 'Flat whole-fleet rates; fixed charges occur once per scenario. No spending authorization.' };
}
// JSON.stringify silently coerces non-finite numbers to null; fail rather than hide overflow.
export function jsonOutput(value) {
  return JSON.stringify(value, (_key, item) => {
    if (typeof item === 'number' && !Number.isFinite(item)) throw new Error('non-finite calculated result');
    return item;
  }, 2);
}
export function main(args = process.argv.slice(2)) {
  try {
    if (args.includes('--help') || args.includes('-h')) { console.log('Usage: remote_compute.mjs setup|status --project PATH [status: --run ID]\n       remote_compute.mjs estimate --rate-low N --rate-high N --hours-low N --hours-high N [--fixed N]'); return 0; }
    const mode = args.shift(), options = {};
    const allowed = mode === 'setup' ? ['project'] : mode === 'status' ? ['project', 'run'] : mode === 'estimate' ? ['rate-low', 'rate-high', 'hours-low', 'hours-high', 'fixed'] : [];
    if (!allowed.length) throw new Error('expected setup, status or estimate');
    while (args.length) {
      const flag = args.shift();
      if (!flag.startsWith('--')) throw new Error(`unexpected argument ${flag}`);
      const [key, inline] = flag.slice(2).split(/=(.*)/s);
      const value = inline ?? args.shift();
      if (!allowed.includes(key) || value == null || value === '' || value.startsWith('--')) throw new Error(`invalid or missing option ${flag}`);
      options[key] = value;
    }
    let result;
    if (mode !== 'estimate') {
      if (!options.project) throw new Error('--project is required');
      const project = fs.realpathSync(path.resolve(options.project));
      result = mode === 'setup' ? setup(project) : status(project, options.run ?? null);
    } else {
      const numericOption = value => {
        const decimal = value.trim();
        if (!/^[+-]?(?:\d(?:_?\d)*(?:\.(?:\d(?:_?\d)*)?)?|\.\d(?:_?\d)*)(?:[eE][+-]?\d(?:_?\d)*)?$/.test(decimal)) throw new Error('expected a decimal numeric option');
        return Number(decimal.replaceAll('_', ''));
      };
      const values = ['rate-low', 'rate-high', 'hours-low', 'hours-high'].map(key => {
        if (!(key in options)) throw new Error(`--${key} is required`);
        return numericOption(options[key]);
      });
      result = estimate(...values, numericOption(options.fixed ?? '0'));
    }
    console.log(jsonOutput(result)); return 0;
  } catch (error) { console.error(`ERROR: ${error.message}`); return 2; }
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) process.exitCode = main();
