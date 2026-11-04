# Evidence and silver-label acceptance

Use separate gates for **artifact fidelity**, **label correctness**, **corpus integrity** and **downstream performance**. Passing one does not imply another. Validation effort should match the intended use; do not turn every useful fixture into a formal proof project.

## Evidence ladder

| Status | What is established |
| --- | --- |
| `authored-unverified` | References were authored; no claim yet that final output agrees |
| `silver-verified` | Named deterministic checks and independent review support specified fields/pages; residual uncertainty and coverage are recorded |
| `adjudicated` | Disagreements resolved under the project’s named expert/human review process |
| `rejected` | A required gate failed; preserve the artifact and cause |

Track status by dimension or region where coverage differs. A reviewed table does not certify a clipped footnote. For OCR of damaged pages, distinguish clean intended text from actually observable content; permit uncertainty or abstention. Keep ambiguous examples out of strict exact-match acceptance until adjudicated.

## Minimal trustworthy bundle

Store the following with accepted fixtures, scaling detail to the task:

- Original authored world/source-layout model and expected content, frozen before rendering/degradation.
- Native and delivered artifact hashes; explicit ordered page IDs and reference hashes.
- Generator/configuration/seed and relevant tool, font, language-data and asset versions.
- Actual applied transforms and coordinate mappings; truthful producer history.
- Label status, inspected pages/regions/dimensions, reviewer identity, localized findings and unresolved limits.
- Dataset membership, source-family ancestry and split declaration for corpus work.
- Raw failures and timings; sanitized delivery reports separate from restricted reports containing source quotations.

A review receipt should identify the exact candidate, labels, spec and checks it examined. Audit and final judge are distinct completed reviews, not two envelopes around one report. Verify scope and hashes before consuming evidence; reject missing required fields, unknown schema/enums, stale identities or incomplete coverage rather than interpreting them as an empty miss list.

Hashes establish identity, not correctness, trustworthy chronology or reviewer independence. Self-authored receipts are not external attestations. For stronger enforcement, have the coordinator capture outputs and hashes outside the Builder’s writable scope.

## Independent checks with valid and invalid controls

**Content:** Validate exact values with their row/column or named-claim context, signs, units, precision, references and rounding rules. Token bags miss permutations; global numeric counters miss swapped balances. Reading-order checks must include omitted/reordered and overlapping sections. Treat nonapplicable dimensions as nonapplicable, not zero.

**Math:** Check structure across correct supported encodings and reject semantic mutations. A matching formula substring elsewhere in prose cannot repair a changed operative equation. Raw-word boxes, extracted text and rendered ink must refer to the same candidate/version before supporting location or visibility claims. Hidden correct text beneath visibly wrong math is a required negative for visibility-sensitive evaluation.

**Visual/native:** Compare authored references with delivered rendering at useful resolution and native structure where relevant. Inspect clipping, overlap, fractions, scripts, tables, captions, rotation, occlusion and inset legibility. Pixel similarity localizes changes; small numeric changes can occupy almost no page area. Render comparison alone does not prove native editability or text-layer content.

**Contract:** Verify counts, page IDs/order, labels, family/split, exact inventory and hash keys. Do not pair pages with unchecked `zip`. Test missing variants, duplicate pages, swapped references, renamed/reordered cross-split reuse and stale review bindings.

**Checker:** Test malformed reports, missing flags, stale dependencies, unsupported states, numeric NaN/infinity, negative timing, contradictory clipping flags and invalid row/page ownership. Include passing controls so stricter checks do not reject correct whitespace, standard notation or valid native geometry. A mocked test demonstrates the mocked boundary only.

For custom math parsers, PDF outline checks or frozen review execution, use the concrete controls in [Math and export regression lessons](math-and-export-regressions.md). These checks distinguish expression equivalence from occurrence ownership, visibility and exact geometric conservation.

Do not use a checker output as its own independent oracle. Freeze or version the checker, retain counterexamples, and revalidate affected evidence when it changes. A validator-only fix can revalidate unchanged artifacts without spending a new rendering round.

## Clone contracts

- Whole-file byte clone: copy then compare input/output hashes.
- Page subset: record separate source/output hashes and selected page order; do not call it byte-identical to the original file.
- Rebuilt verbatim clone: compare normalized visible text, numbers, tables and reading order, plus visual and structural traits. `overlap.py --mode verbatim` does not establish semantic equality.
- Nonverbatim stand-in: compare required difficulty/layout and newly authored labels, not source words or identical pixels.

## Scoring and promotion

Use `judge-rubric.md` for localized misses. `score.py` validates its supported input schema and computes penalties/revision advice. It cannot verify that a reviewer actually inspected a page, that a receipt belongs to this corpus, or that all quality dimensions were covered. The coordinator must establish those separately.

Declare critical gates and quality thresholds before the run. Cosmetic lows may be accepted with disclosure; semantic contradictions, missing required structures, leakage and split contamination block acceptance. Do not average critical failures away. Report pass rate, defect rates by type and hardest slices, review coverage and abstentions alongside any aggregate score.

For large silver sets, check all machine-checkable invariants and all critical numeric/math fields where feasible, then use a predeclared stratified visual/editorial sample including every producer/layout/transform combination and risk extremes. Publish denominators and uncertainty; sample review does not certify every page. Escalate disagreements and expand sampling where defects cluster.

## Cached and measured evidence

Bind reusable results to inputs, labels, scorer/dependencies, extractor/configuration and tool/font/language versions. Preserve originating provenance when reusing a cache; never relabel stale outputs with current identity. Timing samples also need execution metadata and finite nonnegative durations. Use fresh cache-disabled measurements for latency claims unless cache behavior is explicitly the experiment.

Fixture quality and extractor performance are separate evaluations. The first can succeed while the second remains unsupported. A similarity score is not a calibrated probability of correctness or a savings estimate.
