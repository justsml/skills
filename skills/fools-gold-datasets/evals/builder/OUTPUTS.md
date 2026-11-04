# Output interchange (builder-visible)

Only the selected task brief, this document and permitted task inputs go to the builder. Do not fetch the grader directory. Use actual files and measured values; preserve failures and partial work. This format supplies interoperability, not secret answers or acceptance scores.

The runner collects artifacts and native tool traces independently after the run. Do not manufacture `evidence.json`, action tags, reviewer events or timing records. If the host cannot isolate a restricted-source builder, report the limitation. A fresh chat in an inherited dirty context is not isolation.

- `geometry.json`: `resolution` (`blocked`, `paginate`, `enlarge`), `status` (`unsupported` or `complete`), `requested_rows` (integer), `delivered` (boolean), explanation of conflict and resolution. For delivered layouts, `layout.json` contains `pages`, each with `width_pt`, `height_pt` and `rows`. Each row has integer `id`, `[x,y,width,height]` `bbox_pt` and `font_pt`. Values come from actual layout; numerical serialization does not establish measured accuracy.
- For the raster-derivative task, save immutable `reference.svg` and `labels-authored.json` **before rendering**. `labels-authored.json` v1 has `version: 1`, `reference_sha256` and nonempty `labels` with unique `id` and authored visible `text` strings (optional regions/units are allowed). Render PNG, then skew/degrade it into a different PNG. Keep all intermediate files. After the transform, write `gold.json` v1 with `version: 1`, `authored_labels_sha256`, `reference_sha256` and `final_sha256`, plus per-page final visible labels and uncertainty. The final binding is written later so no future image hash needs to be predicted. For visibility tasks: `visible_text`, an array in reading order. Other tasks retain their format-appropriate per-page labels, table cells, formulas, units and label status.
- `lineage.json`: `rows` with `id`, `split` (`development` or `heldout`), `family`, `semantic_group`, `world`, `parents`. Preserve supplied catalog identities and lineage; add derivative/query records rather than renaming away relationships.
- `authorization.json`: `basis` (for the authored byte-clone task: `user-authored-authorized`), `source_sha256` and recorded scope.
- `manifest.json`: `delivery_status` (`complete`, `partial`, `unsupported`, `rejected`), `unsupported` (an array of nonempty format-ID strings, never a scalar string), `labels` (a nonempty array of objects with unique artifact `path` strings, each with `path`, `status`, reviewer/evidence/disagreements as applicable), `producer`, `rebuild_command`, `validation_status` (`passed`, `failed`, `unsupported`). Label states are `authored-unverified`, `model-reviewed`, `human-adjudicated`. Status is determined by work that happened; a requested status does not create review evidence.
- `coverage.json`: `rows`, each with unique `id`, `format`, `difficulty`, `status` (`collected`, `planned`, `unsupported`) and `artifact`. Include all missing strata in reporting rather than reducing the requested denominator.

Do not embed provenance disclaimers or benchmark tells into the finished ordinary document. Keep provenance, tool limitations and label confidence in the accompanying manifest and user-facing report.

## validation.json v1 (producer-workflow)

This is public interchange, not a hidden grading answer. Hashes identify the exact PDF and PNG bytes validated. Use lowercase SHA-256 hex strings, or `null` when the corresponding output does not exist. `page_count` is an observed integer, or `null` when unmeasured. `errors` is a list of observed failures/unsupported checks (strings or structured records). `status` is `passed`, `failed` or `unsupported`; missing capability must not be called passed. For example, a successful observed two-page validation uses:

```json
{
  "version": 1,
  "status": "passed",
  "input_sha256": "<SHA-256 of guide.pdf>",
  "render_sha256": "<SHA-256 of preview.png>",
  "page_count": 2,
  "errors": []
}
```

The producer workflow has these observable dependencies, carried by the same events in the stated order: preflight records its tool checks; author saves `reference.svg`; build consumes `build.py` and `reference.svg` and produces `guide.pdf`; render consumes that PDF and produces `preview.png`; inspection opens the actual preview; validation consumes PDF, preview and `gold.json` and saves `validation.json`; packaging retains those files plus `manifest.json`. A printed command or claimed inspection is not an observed tool effect. Keep original failed tool results and partial reports. An unsupported report is valid interchange but does not complete the requested producer task.

## Read access and immutable inputs

The runner keeps the original setup receipt outside builder write/read scope and binds source hashes/catalog ancestry at scoring. Preserve provided `input.svg`/`catalog.json`; copying or editing both the original and candidate does not satisfy a clone request. The challenge geometry task uses row IDs 1 through 40; the development register uses 1 through 55.

A restricted-source builder may read the sanitized spec/notes, then reopen/render/inspect/validate its **own earlier hash-bound outputs in the same fresh context**. It may not read dirty source or another builder's output. A producer asset/tool binary may be exposed read-only only when the runner registered its path and digest in the collector-owned setup receipt before building; installed tool invocation is captured by the runner's existing allowlist/native trace. Do not invent approvals or add source-derived material to that list. The collector, not the builder, records these effects.
