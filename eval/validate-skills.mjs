#!/usr/bin/env node
import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
// This repository intentionally uses single-line frontmatter scalars. Fail on
// multiline metadata rather than silently misinterpreting a skill's catalog.
export function metadata(text, location) {
  const m = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/.exec(text);
  if (!m) throw new Error(`${location}: missing frontmatter`);
  const fields = {};
  for (const line of m[1].split(/\r?\n/)) {
    if (!line.trim() || line.trim().startsWith('#')) continue;
    const kv = /^([a-z-]+):\s*(.*)$/.exec(line);
    if (!kv || !kv[2] || /^[>|]/.test(kv[2])) throw new Error(`${location}: only single-line metadata supported`);
    if (kv[1] in fields) throw new Error(`${location}: duplicate ${kv[1]}`);
    fields[kv[1]] = kv[2].replace(/^(["'])(.*)\1$/, '$2');
  }
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(fields.name ?? '') || fields.name.length > 64) throw new Error(`${location}: invalid name`);
  if (!fields.description?.trim() || fields.description.length > 1024) throw new Error(`${location}: invalid description`);
  if (fields['disable-model-invocation'] !== undefined && !['true','false'].includes(fields['disable-model-invocation'])) throw new Error(`${location}: invocation flag must be boolean`);
  if (!text.slice(m[0].length).trim()) throw new Error(`${location}: missing instructions`);
  return fields;
}
export async function validateSkills() {
  const entries = (await readdir(path.join(root,'skills'),{withFileTypes:true})).filter(e=>e.isDirectory());
  const seen = new Set();
  for (const entry of entries) {
    const source = `skills/${entry.name}/SKILL.md`;
    const fields = metadata(await readFile(path.join(root,source),'utf8'),source);
    if (fields.name !== entry.name) throw new Error(`${source}: name must match directory`);
    if (seen.has(fields.name)) throw new Error(`${source}: duplicate name`);
    seen.add(fields.name);
    let yaml = '';
    try { yaml = await readFile(path.join(root,'skills',entry.name,'agents/openai.yaml'),'utf8'); }
    catch(error) { if(error.code !== 'ENOENT') throw error; }
    // Report asymmetry for human review. These hosts support different policies.
    const claudeManual = fields['disable-model-invocation'] === 'true';
    const codexManual = /^  allow_implicit_invocation:\s*false\s*$/m.test(yaml);
    if (claudeManual !== codexManual) console.warn(`REVIEW ${entry.name}: Claude manual-only=${claudeManual}, Codex manual-only=${codexManual}`);
  }
  console.log(`Validated ${seen.size} skill metadata contracts`);
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  validateSkills().catch(error=>{ console.error(`ERROR ${error.message}`); process.exitCode=2; });
}
