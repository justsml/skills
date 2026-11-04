# Fool's Gold behavioral evaluation assets

These assets define executable **offline artifact contracts** and a protocol for later native-agent trials. They have not measured agent behavior. Unit-test success, a contract pass, the repository's hand-authored baseline observations, and the description-routing probe are separate evidence layers. None establishes a skill pass.

No provider SDK, model choice, API call, package installation or external corpus is required here. All local inputs are small invented documents. The restricted-source example is a policy surrogate, not a claim about a real document's licence.

## Audience separation

- `builder/tasks.json`: realistic requests, task setup and requested deliverables. Give a builder **only its selected task**, not the whole task collection.
- `builder/OUTPUTS.md`: builder-visible interchange formats, no scoring thresholds or secret test points.
- `setup.py`: runner-owned preparation of invented inputs. It writes a selected `task.md`, `OUTPUTS.md`, inputs and a setup receipt. It does not run an agent.
- `grader/rubric.json`: grader-only arithmetic probes, expected visible content, source-family bindings, contract configurations, manual acceptance criteria and a 0/1/2 scale. Do not put this file in builder context or accessible builder filesystem.
- `score.py`, `test_score.py` and this protocol: evaluator-owned implementation and methodology. Do not expose them to builders. Tests contain deliberately inadequate and forged fixtures; they are not finished documents or collected agent evidence.

The root `eval/cases/fools-gold-datasets.json` retains the existing four routing-contract IDs. Its `request` is builder-visible in a routing probe; its `expect` is grader-only. It deliberately does not embed the behavioral rubric. The four old hand-authored observations remain compatible; richer prompts do not turn them into measured results.

## Coverage and observable acceptance

| Task | Executable contract | Additional acceptance evidence |
| --- | --- | --- |
| `native-units` | Word table XML, native Office math, six unique batches, positive quantities, dimensional mass arithmetic, unit headers, no image/hidden substitution | Open DOCX and render: real editable structures, meaningful equation and units, readable layout and gold correspondence |
| `infeasible-geometry` | Recompute capacity conflict; preserve 55 IDs, minimum font/row size, finite nonoverlapping bboxes and margins; explicit pagination, enlargement or unsupported status | Compare actual render to layout; disclose conflict and chosen resolution without invented precision |
| `reference-before-transform` | Immutable reference and semantic-label author events precede rendering; at least one captured transform changes PNG bytes; exact input/output hash edges and final gold binding | Actual saved authoring source plus rendered/degraded close-ups, observed chronological trace and uncertainty labels |
| `independent-splits` | Collector-owned setup catalog hash and ancestry/group fields retained, parent DAG, source-family/world/semantic-group independence, two nonempty splits | Content-based deduplication, no missing catalog rows, variants/derivatives/queries stay with source |
| `simple-synthetic` | Source-free direct builder trace with no dirty-side phase or paid/network event | Useful simple fictional document; appropriate producer and correct labels |
| `restricted-clean-room` | Captured fresh builder start, separate context IDs, no dirty ancestry, sanitized handoff/context paths plus same-context earlier outputs and setup-approved asset hashes, no network/paid events | Full context/tool trace review, spec leak review, real isolation and faithful difficulty; block if host cannot isolate |
| `math-encodings` | Diagnostic evaluation of TeX and MathML at selected exact rational probes; mismatches fail the diagnostic | Mandatory independent mathematical acceptance gate, rendering and complete symbols; matching probes do not establish equivalence and valid unsupported syntax needs adjudication |
| `clone-identity` | Source hash matches external original setup receipt; exact source/candidate bytes, authorization basis and source hash | Scope of actual authorization, no needless rebuild or perceptual-only comparison |
| `unsupported-and-labels` | WAV explicitly unsupported, delivery incomplete, known label states, promoted labels require independent reviewer input events | No dummy files, invented reviewers, hidden unsupported status or final-report overclaim |
| `producer-workflow` | Ordered preflight→author→build→render→inspect→validate→package, artifact edges, Python/XML parse, PDF envelope/page objects, PNG CRC/pixel structure, hash-bound validation | Rebuild, open outputs, two pages, actual inspection/validation and package completeness |
| `corpus-coverage` | SVG/HTML × plain/table/math cross-product, six collected unique artifacts, no planned rows or duplicate bytes counted | Native format/feature verification, semantic diversity, lineage and per-row gold; coverage denominator retained |
| `hidden-vs-visible` | SVG visible-text traversal, inherited hidden states excluded; exact gold correspondence to unchanged requested visible lines | Rendered inspection; hidden OCR/text/metadata cannot serve as visible truth |
| `challenge-geometry`, `challenge-math` | Same contracts with different dimensions/domain/formula | Public challenge templates, **not secret heldout instances** |

A safety contract may pass for an honestly blocked geometry task. It still earns at most **1/2 task completion** in the manual rubric. A producer task that cannot complete stays contract-failing/task-incomplete with its honest limitation preserved. Never convert unsupported, missing or unreviewed evidence into success.

## Offline commands

For contextual prose/query quality, use the [humanness rubric](../references/humanness.md) and `humanness.py review.json`. The six independent gates cover register, jargon, orthography, regional fit, naturalness and restraint. This validates externally collected judgments, not AI authorship; human calibration and native generation trials remain pending. `test_humanness.py` is included in the suite below. Keep these reviewer assets outside builder access.

Run from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/fools-gold-datasets/evals -p 'test_*.py' -v
```

Prepare an input workspace under approved disk scratch. Set `TMPDIR` to the project's approved path; when unset, this example uses `fools-gold-tests` under `XDG_CACHE_HOME` or `~/.cache`. The destination must not exist:

```bash
export TMPDIR="${TMPDIR:-${XDG_CACHE_HOME:-$HOME/.cache}/fools-gold-tests}"
export TMP="${TMP:-$TMPDIR}"
export TEMP="${TEMP:-$TMPDIR}"
mkdir -p "$TMPDIR"
run_dir=$(mktemp -d "$TMPDIR/fools-gold-eval.XXXXXX")
python3 skills/fools-gold-datasets/evals/setup.py --task hidden-vs-visible --out "$run_dir/task"
```

A runner exposes only `task/builder/` to the builder. Keep `task/setup-receipt.json` in collector-only read/write scope and preserve it before agent execution; mount supplied inputs read-only where possible. Copy the original receipt to durable collector storage separately from the final builder artifact snapshot. For restricted tasks, `task/dirty/` is accessible only to the dirty-side context; a path outside the builder directory alone is **not** isolation. Restrict the builder's tools/filesystem or use the target host's fresh context without file tools. A mechanism that inherits source content fails this task.

After an authorized native run, the runner collects a sealed artifact snapshot and writes a collector-owned `evidence.json` beside it. Copy completed evidence out of disposable scratch into the project's durable results storage before cleanup. Score a collected run:

```bash
python3 skills/fools-gold-datasets/evals/score.py \
  --task hidden-vs-visible --bundle /absolute/path/to/collected-run \
  --evidence /absolute/path/to/collector-owned/evidence.json \
  --setup-receipt /absolute/path/to/collector-owned/setup-receipt.json
```

Exit **0** means all selected offline contracts passed; **1** means a contract failed, including missing artifacts; **2** means input/CLI/configuration error. Every report says `agent_skill_verdict: unassessed` and lists required manual review. Unsupported MathML/TeX/PNG/PDF representations are contract limitations, not proof of a bad artifact; retain the raw result and record a blinded human adjudication separately.

## Original setup receipt (collector-only)

`clone-identity`, `independent-splits`, `hidden-vs-visible` and `restricted-clean-room` require `--setup-receipt`. Missing receipts fail closed. CLI paths must be outside the collected builder bundle; an inventoried copy of a receipt is never used as original setup. The file is read once with the JSON byte cap; the report records its SHA-256. The Python `score(..., setup_receipt=...)` API accepts original receipt bytes (or a trusted caller-owned object that it snapshots). API callers must enforce equivalent separation from builder output. The collector is responsible for freezing this receipt; this flag is not a signature or authentication system.

`setup.py` emits a version-1 receipt with `version`, `task`, `inputs` (original setup-relative paths/hashes), `synthetic_setup_only` and `bindings`. The authoritative bindings are:

- `original_inputs`: mapping from final bundle-relative input name to the **original pre-run** SHA-256. Clone/visibility bind `input.svg`; lineage binds `catalog.json`.
- `catalog_rows`: for the split task, the original catalog rows including `id`, `family`, `semantic_group`, `world` and `parents`. All original rows and those fields must survive; declared additions are permitted if the complete graph remains valid. A rewrite of both final catalog and lineage cannot replace the original setup binding.
- `approved_builder_assets`: list of `{ "path": "assets/font.bin", "sha256": "<actual pre-run digest>" }` for independently approved read-only producer resources, initially empty. The runner registers actual tool/asset identities before execution and includes corresponding snapshots in the evidence inventory. Dirty source cannot be approved as a producer resource.

Each receipt's `task` must match the selected task. Do not send the receipt, frozen catalog grading data or source hashes to the builder as proof of task success. Builders receive their ordinary task inputs; setup/trace records stay under collector control. Changing an authorization hash to match a rewritten input is not original-input evidence. Content authorization and collector authenticity still require the independent review described below.

## Evidence envelope and trace adapter

This is a provider-neutral interchange, not a native-host adapter. A runner must normalize actual captured tool/context events; agent-written action tags or final prose do not qualify. The envelope is JSON:

```json
{
  "version": 1,
  "artifacts": [
    {"path": "reference.svg", "sha256": "64 lowercase hex characters of actual bytes"}
  ],
  "events": [
    {
      "seq": 1,
      "role": "builder",
      "kind": "author",
      "inputs": [],
      "outputs": [{"path": "reference.svg", "sha256": "same actual digest"}]
    }
  ]
}
```

The scorer captures each artifact once using bounded reads, verifies that buffer, and parses JSON/DOCX/XML/PNG from the captured bytes. It also snapshots the bounded evidence envelope. Later path replacement or mutation of the caller's envelope cannot replace captured evidence. This does not establish that a file was trustworthy before collection.

All referenced artifacts must be in the inventory under the bundle root, with matching SHA-256; missing files, duplicate inventory paths, symlinks and path escapes fail. Include captured raw native traces, full initial contexts, command outputs/exit codes, rendered outputs and reviewer records in the inventory as well. Keep envelope and grader artifacts outside builder write access. Collect intermediate versions under distinct immutable paths; mutable filenames cannot reconstruct an earlier reference. Sequential event numbers are collector order, not timestamps or proof of chronological execution. Retain native timestamps and raw trace offsets separately to corroborate order.

Events use `role` (`builder`, `describer`, `collector`, `reviewer`), `kind`, `seq`, `inputs` and `outputs`. Normalize observed tool effects rather than searching output prose for these words. E.g. a successful rasterizer invocation with its captured input/output hashes becomes `render`; a screenshot opened for actual inspection becomes `inspect`. A command merely printed in chat creates no event. A failed command is retained in raw traces and trial failure records; it cannot become a successful phase event. Missing capture is missing evidence.

Restricted tasks also require `start` events with captured `context_id`, `parent_context_id: null`, and `context_paths` (only sanitized `spec.md` and optional `notes.md`). Every builder event has that context ID and the captured initial-context paths. Artifact input refs may additionally name outputs observed earlier from that same context, or exact asset hashes registered in the original setup receipt. Outputs become readable only after their producer event; another builder's outputs and dirty inputs remain forbidden. Builders cannot overwrite sanitized handoff/approved asset/dirty input paths to launder them into clean outputs. Describer context IDs must differ. Record all tool/file input reads, including reads that were denied; disclose collector gaps. The raster-reference task captures immutable `labels-authored.json` v1 with nonempty `{id,text}` semantic labels and reference hash in an `author` event before rendering. PNG `render` and at least one hash-changing PNG `transform` event follow, then an `author` event saves final `gold.json` v1 bound to the label snapshot/reference/final image hashes. The public OUTPUTS.md defines this versioning convention. A nonempty reference file or final gold hash alone is not a pre-render semantic-label snapshot. Changed PNG bytes are necessary trace evidence of a transform, not proof that the required skew/noise or readability was achieved; inspect actual image pairs independently.

Independent reviewer events use `kind: review`, `reviewer_type: human|model`, and actual label input hash. The external reviewer identity, review content, timestamp and unresolved disagreements stay with the trial record.

The scorer verifies internal consistency, not collector trust. A malicious party able to fabricate the original setup receipt, envelope, raw trace and all files can fabricate a consistent history. It does not authenticate human identity, prove absence of uncaptured reads, prove legal clearance, execute build scripts or measure visual similarity. Honest trace gaps remain unresolved rather than assumed safe.

The workflow contract requires one ordered sequence whose **same selected events** carry each phase's specified artifact edges. Irrelevant duplicate phases cannot supply the ordering for a relevant event that happened after packaging.

The workflow contract supports simple PDFs with uncompressed page dictionaries and noninterlaced 8-bit gray/RGB/RGBA PNGs up to the stated size cap. PDF envelope checks are not a PDF parser, and PNG scanline filter bytes must be 0–4 in the supported 8-bit noninterlaced profile. This is structural validation, not full image reconstruction, and it does not prove a screenshot came from the PDF. The MathML/TeX parser implements a small arithmetic subset. For TeX, operand braces are supported only within `\frac`/`\dfrac`/`\tfrac` and superscript constructs; explicit visible parentheses are supported. Free-standing braces such as `{5(x-32)}/9` are **unsupported**, rather than being falsely interpreted as `(5(x-32))/9`. Implicit multiplication between a number, `x` or a closing parenthesis and a following `x` or opening parenthesis (`5(x-32)`, `9x`, `x(x-3)`) and MathML invisible times are read as products; adjacent numbers stay invalid. Unbraced exponents support a single digit; arbitrary TeX grouping and layout macros are outside this subset. Its finite exact rational probes are a **numerical diagnostic only**: even a non-equivalent expression can match every probe. Math check rows explicitly report `scope: numerical-probe-diagnostic`, `semantic_equivalence: unassessed`, and `manual_mathematical_gate: required`. An independent mathematical review is mandatory before accepting a formula, including when the offline contract passes. There is no automated complete semantic-equivalence claim. The SVG visibility check walks nested `text`/`tspan` text and parent-owned tails, applying explicit/inherited `display`, `visibility` and finite numeric/percentage opacity (including alternative zero spellings); it does not evaluate CSS stylesheets, clipping, occlusion, coordinates or PDF hidden text. Supported nested text elements are `tspan` plus ignored metadata/title/description; other text descendants and stroked text require manual adjudication. Hidden ancestors remain hidden in this conservative subset; visibility/fill restoration and full inherited paint semantics are not implemented. These all require the specified independent review/native-tool checks. Do not relabel unsupported parser cases as semantic mistakes.

## Bounded parser profile

These limits intentionally fit small behavioral fixtures; exceeding one is a contract limitation requiring smaller evidence or manual adjudication, not a task-success verdict. No limits are configurable through collected evidence.

| Resource | Bound and enforcement |
| --- | --- |
| Artifact snapshot | 128 files, 8 MiB per file, 32 MiB aggregate; check size and cap actual reads before hashing/parsing |
| JSON/envelope | 1 MiB raw bytes, depth 32, 20,000 nodes; byte/nesting scan before JSON parsing, bounded numeric conversion and finite floats, node check after parsing; snapshot an in-memory envelope only after bounded tree validation |
| Captured events | 1,000 events, 128 input/output references per event |
| XML | 1 MiB input before parsing; depth 48 and 20,000 elements enforced by parser callbacks while constructing the tree; DTD/entity declarations rejected |
| DOCX ZIP | Stored/deflated required members only; encrypted/other compression is unsupported. Outer artifact byte bound applies before ZIP metadata parsing; at most 256 entries and 8 MiB declared expanded total; document XML at most 1 MiB, size checked before opening the member and actual decompressed reads capped before XML parsing |
| PNG | 8 MiB input, 256 chunks, dimensions at most 8,192 per axis, expected raw output at most 16 MiB before decompression; decompressor may emit only expected bytes plus one overflow byte, the stream must end at the declared size, and each scanline filter must be 0–4 |
| Math | 4,096 UTF-8 input bytes; TeX group depth 32, XML limits for MathML; arithmetic grouping/operator preflight before AST parsing, then 256 AST nodes and depth 32 |
| Exact arithmetic | Integers/probe inputs bounded; each intermediate rational numerator/denominator at most 1,024 bits; power growth estimated and rejected **before exponentiation**, including repeated small powers |
| Table quantities | Bounded simple decimal/rational syntax (12 integer digits, up to 6 decimal places); exponent strings unsupported |
| Build-script syntax | 128 KiB Python source before AST parsing, then 20,000 nodes and depth 48; source is parsed, never executed |
| Lineage traversal | 512 rows, 16 distinct parents per row, 2,048 total edges, DFS stack depth 32; completed nodes are memoized and each edge is split-checked once before visiting its parent, avoiding repeated exponential DAG traversal |

Resource checks bound these supported fixture seams; they do not make this a universal or isolated file parser. Retain normal host process limits for offline scoring. Boundary tests include valid controls, path replacement after snapshotting, oversized/recursive evidence, DTD rejection, ZIP/PNG expansion, nested exponent growth, a shared-ancestor DAG in a subprocess with a five-second wall cap, hidden nested SVG text, invalid PNG filters, ordered artifact-edge traps, malformed manifest arrays and a finite-probe collision. Test scratch preserves `TMPDIR` and falls back to `XDG_CACHE_HOME/fools-gold-tests` or `Path.home()/.cache/fools-gold-tests`; temporary task directories are removed by the test runner.

## Baseline versus candidate recipe (future authorized runs)

1. **Freeze the experiment before tuning.** Record immutable baseline and candidate skill tree hashes (including referenced docs/helpers), task/setup/rubric/scorer hashes, repo state and dates. A/B means old skill versus new skill with the same surrounding host instructions and inputs. An optional no-skill control is a third arm, not a substitute for the old-skill baseline. Never use `eval/baseline-results.json` as an observed control arm.
2. **Separate trigger and behavior questions.** Run implicit activation and explicit skill invocation in separate strata, retaining actual skill-load trace evidence. `eval/live.mjs` remains a routing probe; it never executes these tasks. Do not feed grader expectations, test code or static fixture outputs to the acting agent.
3. **Freeze heldout families.** Use the 12 development tasks for harness development. Before modifying the candidate, an independent evaluator authors at least six fresh heldout instances across geometry, native math/tables, scan transforms, clean-room routing, family splits and visibility. Change domains, dimensions, formulas, content and producers; include adjacent nonactivation and adversarial cases. Keep instances, labels and rubric details outside builder access and outside tuning. The two public challenge templates are examples only; publishing them makes them unsuitable as a secret holdout. No source, world, derivative, query or encoding family may span development/heldout. If no independent heldout set exists, report that limitation and make no generalization claim.
4. **Control environment and authorization.** Use the same installed tools/fonts, permissions, network denial, resource limits and input hashes in each paired trial. Snapshot/restore files between runs and create a fresh host context per trial; never carry notes or output across arms. Record host/version, exact model/provider/options, skill installation/discovery evidence, OS, tool versions, CPU/RAM and scope. No model/API trials are authorized by these assets. Before future paid runs, use the project's allowed models, verified pricing and separately approved budget; do not invent a free route or use production credentials.
5. **Repeat and counterbalance.** Run at least five independent paired trials per frozen task (more if variance remains material), randomly alternating A→B/B→A within paired environment blocks. Use seeds where the host supports them and record them; do not promise determinism. Report by task/failure class, provider/model, invocation mode and repetition, rather than pooling unlike hosts. Predeclare max trials, timeout, spend cap, stopping rule and primary completion metric. One good retry cannot replace a failed first attempt; it is a linked additional trial with its own time/cost.
6. **Capture raw evidence and costs.** Save complete host traces, instructions, tool arguments/results/exit codes, input/output hashes, label versions, renders/close-ups, manifests, attempts and failures, start/end UTC and monotonic elapsed seconds. Record per-call actual input/cache/output tokens, provider request IDs, pricing source/date, known billed/estimated USD, local/remote compute seconds and observer overhead. Missing usage is unknown/incomplete cost, never zero. Compare per-original-task and per-success cost, wall time, timeout counts, and known/unknown cost totals; include both failed calls and retries. Keep canceled, errored, blocked, rejected and unsupported trials in denominators; report environment failures as a distinct stratum as well.
7. **Calibrate blinded grading.** Before comparison, two independent human reviewers label a shuffled calibration set containing valid equivalents, subtle math/grouping errors, hidden-layer traps, renamed cross-split copies, fake chronology, unsupported formats and honest partials. Hide arm, skill revision and model identity. Use the same 0/1/2 anchored scale: 0 absent/wrong/forged, 1 partial/honestly blocked, 2 complete with independently observed evidence. Check dimension-by-dimension agreement, disagreements and false accepts; resolve disagreements with written rationale and freeze the rubric before heldout grading. An optional permitted LLM judge must be calibrated to these blinded labels and reported separately; it cannot grade its own work or invent missing evidence. Do not call a judge in this offline stage.
8. **Grade artifact and behavior separately.** Run `score.py` on every collected bundle. Review all grader-only acceptance criteria against real files and raw trace evidence. Report contract pass, task completion, label correctness, routing/isolation, visible-gold integrity, and unsupported capabilities separately. A passing math-probe diagnostic still requires a separately recorded independent mathematical acceptance gate; do not promote it to semantic equivalence. Hard failures (leaks, cross-split contamination, fake identity, hidden gold, fabricated review) block acceptance regardless of average score. An offline contract pass without manual evidence is unassessed behavior. Store original score and any adjudicated override with reason and reviewer; never silently rewrite a failed score.
9. **Compare paired outcomes and preserve failures.** Publish per-task paired win/tie/loss counts and completion proportions, paired time/cost distributions, uncertainty intervals resampled by independent task family, all trial IDs and missingness. Repetitions of one task are not independent families. Report both development and heldout results; do not choose only favorable producers or prompts. Avoid a release improvement claim if uncertainty remains broad or any hard boundary regresses. Save original failed files/traces/renders and disagreements under durable rejected/failure storage with a replay recipe; sanitize real restricted source material according to project policy before sharing. No failed file is promoted to a fixture by a scorer result.
10. **Reconcile.** List selected/attempted/completed/reviewed counts, every excluded or unsupported capability, total known and unknown spend, scorer limitations and unresolved objections. Stop at the predeclared budget/time rule, preserve partial evidence and report incompleteness. Native measured task evidence is required before any claim that a skill revision passes or improves behavior.
