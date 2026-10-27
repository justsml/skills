---
name: fools-gold-datasets
description: Generate realistic synthetic documents, recordings, and silver evaluation datasets with authored labels and verified artifacts. Use for original fixtures, clean-room stand-ins that preserve extraction difficulty, authorized clones, mixed scan/native corpora, and retrieval, search, RAG and Q&A evaluation sets. Not for ordinary document summaries or edits.
---

# Fool’s Gold Datasets

Produce useful, believable artifacts with **traceable silver labels**. A convincing page, a successful export, and a trustworthy reference are different achievements. Report each separately. Optimize for meaningful content, realistic structure, diverse difficulty and measured label reliability—not the number of files or review rounds.

## Choose the shortest valid route

| Request | Route |
| --- | --- |
| Original synthetic data, no protected source to imitate | Author directly from a domain model; no artificial clean-room loop. Independently review the result. |
| Match a restricted source’s difficulty or layout | A source-aware **Describer** writes a sanitized specification; a fresh, source-blind **Builder** creates new content. |
| Reuse permitted content | Record license/authorization and its conditions. Rebuild directly when appropriate. |
| Byte-identical whole-file clone | Copy bytes and verify both SHA-256 hashes. Page extraction, re-saving and re-distilling are derivatives, not byte clones. |

Infer `synthetic` for an original dataset. For source replacements, choose `synthetic`, `public-domain-swap`, or `paraphrase` from the user’s intent and rights; use `verbatim` only with permission. Public access alone is not reuse permission. A paraphrase or clean-room procedure does not itself establish legal clearance.

Read only the references needed:

- **Finding input documents/media:** [sourcing-inputs.md](sourcing-inputs.md).
- **Retrieval, search, RAG or Q&A eval sets:** [references/retrieval-questions.md](references/retrieval-questions.md).
- **Writing a buildable contract:** [spec-format.md](spec-format.md).
- **Tables, math, native exports, scans or other media:** [production.md](production.md).
- **Many families, variants, training/tuning/test splits:** [references/corpus-design.md](references/corpus-design.md).
- **Checks, labels and acceptance:** [references/verification.md](references/verification.md) and [judge-rubric.md](judge-rubric.md).
- **Testing or improving this skill:** [references/skill-evals.md](references/skill-evals.md); [evals/](evals/) contains task assets.
- **Choosing an alternative method:** [references/strategies.md](references/strategies.md).

For retrieval/Q&A datasets, follow the dedicated reference: persona style comes from authorized real questions, facts come from source page images, and pooled page relevance, answer correctness and realism are checked separately. Preserve judged negatives and a blind different-model check before accepting silver cases.

## Establish the contract

Record purpose, output formats, audience/domain, content rights, difficulty features, approximate size, available tools, time/cost limits and desired confidence. Decide where synthetic provenance belongs: always in the manifest, and in visible notices when the requested use/distribution needs them. A realism eval may deliberately keep notices out of model inputs; a publicly circulated example may need them. Do not add or penalize notices through an unstated judge preference. Reuse session authorization; ask only about consequential unknowns. Keep policy and artifacts in the target project, not this skill installation.

Separate **hard requirements** (visible values, native table structure, minimum readable size, protected split, required challenge) from **preferences** (line count, exact spacing, incidental metadata). State which dimensions are fixed and which may reflow. For a matched fixture, measure the actual source; do not invent word budgets from a bounding box. For an original corpus, do not inherit a source’s accidental geometry constraints.

Predeclare success before authoring: required visible content, label fields, inspection coverage, critical failure gates and quality rubric. Choose a small pilot spanning the hardest mechanisms and distinct producers. A one-page preview does not establish multipage capability.

Resolve this file’s installed directory as `FOOLS_GOLD_SKILL_DIR`. Use project scratch/cache locations, available dependencies and approved isolation for untrusted files. `check_deps.py --plan` is a tool inventory/install hint, not permission to install or spend. Check bytes, inodes and quota before large runs. Pin relevant tool/font versions. Use project-approved models and logging; record actual usage and cost, with unknowns explicit.

## Build in five stages

### 1. Author the world and its references

Write structured facts before prose: entities, dates, quantities with units and precision, table cells, chart series, formula ASTs, assumptions and claim dependencies. Give every page, block, cell and equation a stable ID. Make the document answer a real reader’s questions; write the result, interpretation, limits and decision in natural prose.

Author expected content before rendering or degradation. Store semantic facts separately from display strings and expected reading order. Derive consistent views from that model, but check arithmetic and meaning independently: generator and label agreement alone can share the same bug.

For restricted-source work, read [spec-format.md](spec-format.md) and use a fresh Builder receiving only the checked spec and abstract revision notes. Source bytes, extracts, metadata strings, screenshots, failed candidates containing leaks, and quote-bearing audits stay on the restricted side. Source-blind prompts on a shared filesystem are process separation, not a security boundary; use scoped tools/filesystem access when confidentiality requires enforcement. Source access/reuse permission does not imply provider-sharing permission. Before sending restricted bytes, renders, transcripts, metadata or source-bearing reports to a hosted Describer or judge, verify that existing authorization covers that destination and retention policy. Otherwise use a local source-side process or a human-written sanitized spec. Reuse clear prior authorization; ask only for missing scope.

### 2. Prove layout and the producer

Use real table/cell objects and a proper math typesetter. Measure shaped text, glyph ink, padding, equation ascent/descent and captions using the **actual** fonts and export path. Resolve infeasibility before bulk authoring: wrap a header with units, allocate a continuation, rebalance permitted columns, or explicitly revise an impossible contract. Preserve values, units, precision, reading order and readability.

Render the smallest representative artifact. Add a short multipage proof only when the requested output or claimed capability spans pages; a single-page fixture need not generate extra documents. For Office workflows, save, close, reopen the saved native file and export that exact artifact. Inspect editable structure as well as pixels. A small component pasted from another producer does not establish a second whole-document production path.

Review actual full pages and readable close-ups early. A useful first preview is better than a large set of unrendered specifications. See [production.md](production.md) for format-specific checks.

### 3. Freeze and generate controlled variants

Freeze the authored model, labels, generator, assets, fonts, configuration and accepted native output before rasterization. Record hashes and stable identities. Preserve failed revisions separately; do not overwrite the evidence used to justify a decision.

Apply each transformation with a recorded seed, parameters, input/output hashes and coordinate mapping. Distinguish storage-only rewrites from visible degradations. Remove native text beneath intentionally rasterized regions; preserve independent inset-source documents and their relationships to surrounding commentary. Verify each changed mechanism against the authored references. Keep original and transformed siblings in the same split.

Parallelize independent family authoring, isolated producer jobs, deterministic checks and independent reviews. Give each writer exclusive paths and each Office process its own profile/output directory. One integrator owns a frozen release. Do not let reviewers consume mutable output or share each other’s conclusions.

### 4. Review what was actually delivered

Run cheap structural/semantic checks first, then independently inspect native structure, rendered content and labels. Review critical values, math, qualifiers and reading order at block/cell level; page-wide token overlap or pixel similarity cannot certify them. Inspect changed pages after repairs and representative hard/failing cases, not just the best examples.

Use [references/verification.md](references/verification.md) to bind evidence to exact artifacts and report coverage. A judge receives candidate renders **and labels**, plus the appropriate source/spec. Models report localized misses and evidence; deterministic code aggregates. An empty report is meaningful only for a completed, identified review with declared coverage.

A missing block, wrong value/unit, leaked source, contradicted label, split contamination or failed required mechanism blocks acceptance regardless of cosmetic score. Unsupported checks remain incomplete, not passed. Preserve label status per dimension: `authored-unverified`, `silver-verified` for a named scope, `adjudicated`, or `rejected`. The label “gold” is reserved for the project’s independently established standard.

### 5. Repair the cause, then scale

For a correct contract with a local defect, revise the build. For an infeasible/ambiguous contract, revise the spec and record the reason; do not repeatedly polish around the contradiction. For a checker defect, fix it with valid and invalid controls and revalidate unchanged artifacts; a validator repair is not a new content build.

For source-matching work, `score.py` supplies bounded revision advice (default three spec attempts, four build rounds each). Its legacy 85-point pass is **rubric arithmetic**, not dataset acceptance. Use the project’s declared quality and evidence gates; do not change a threshold after seeing results. Larger user-authorized budgets remain ceilings, not targets. For original generation, use the same bounded repair principles without manufacturing source-blind roles.

Stop a non-improving lane, preserve its best result and explain the unresolved cause. Try a different producer or a smaller mechanism proof when warranted. Once the pilot passes, expand the predeclared panel, validate exact membership, and inspect the new combinations. Publish accepted and rejected counts, coverage, limitations, costs and actual page/media samples. Deliver native sources, rendered files, labels, manifest, recipes and sanitized review evidence; keep restricted originals and quote-bearing reports out of the package.

## Helpers and their limits

Run helpers from this installed directory; use `--help` for options. They are diagnostics with explicit scope, not a universal acceptance engine.

| Helper | Useful evidence |
| --- | --- |
| `check_deps.py` | Tool/font availability and installation planning |
| `select_pages.py` | Heuristic diversity sampling and derived page/span extraction |
| `overlap.py` | Lexical overlap, denylist and length diagnostics; not legal clearance or semantic fidelity |
| `check_tells.py` | Candidate realism flags for contextual adjudication |
| `file_profile.py` | Restricted-side file traits; only explicitly sanitized, inspected output may cross the source boundary |
| `pixel_diff.py` | Visual localization for matched rendering; not value correctness or text-layer equivalence |
| `pdf_variants.py` | Controlled storage/render variants; inspect actual output and provenance |
| `score.py` | Validated miss-report arithmetic and bounded loop advice; not proof of review completion |

Keep actual producer provenance. A genuine ReportLab export is not a defect simply because it identifies ReportLab. Stamp alternate metadata only as an explicit test factor, with real production history retained externally. Contextual words such as “sample” in a laboratory report are not automatically generation tells; preserve raw flags and adjudicate exact occurrences rather than rewriting meaningful content to evade a checker.
