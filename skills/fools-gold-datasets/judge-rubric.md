# Miss report and judge rubric

The source-aware audit (when source matching applies) and independent final judge return the same miss report. `score.py` turns it into the score and the next decision. Models list misses; the script does the arithmetic.

## Inputs

- source pages/transcript only for source matching and only on the authorized source-aware side; otherwise the original authoring contract
- the candidate's final rendered pages or transcript and native structure evidence
- the actual label artifacts: ordered page/block IDs, cells, equations, expected text and uncertainties
- exact candidate, spec, label and checker hashes; reviewer identity and inspected coverage
- `spec.md` and the mode
- applicable deterministic checks: source-overlap only for source matching, plus layout/content checks required by the contract

## Output (JSON only)

```json
{
  "misses": [
    {
      "category": "table",
      "severity": "high",
      "cause": "spec",
      "where": "p2.b3",
      "summary": "header row spans cols 2-3 in the source; spec described a plain grid",
      "evidence": "optional, may quote the source, dirty side only"
    }
  ],
  "structural_fidelity": 0.0,
  "difficulty_parity": 0.0,
  "notes": "optional free text for the Orchestrator"
}
```

An explicit empty `misses` list means no misses were reported in the inspected scope. It does not prove a completed review, full coverage or fixture acceptance. The coordinator verifies identities and coverage separately; missing/malformed reports are errors. `structural_fidelity` and `difficulty_parity` (0–1) are diagnostics recorded in the manifest. The rubric decision comes from `score.py`; [verification.md](references/verification.md) defines the additional evidence needed for acceptance.

## Categories

| category | covers |
| --- | --- |
| `format` | container, version, page/slide/sheet count, page size, codec, duration |
| `layout` | block positions, columns, margins, z-order |
| `reading-order` | order an extractor would read blocks in |
| `typography` | font classes, sizes, weight, leading |
| `table` | shape, merged cells, header rows, cell content type |
| `figure` | images, charts, captions and their links |
| `difficulty` | a difficulty feature missing or made easier |
| `content-length` | declared per-block length/density constraints and their frozen tolerances |
| `content-meaning` | paraphrase lost meaning; swap or synthetic content incoherent |
| `mode` | any other content-mode rule broken |
| `leak` | source phrase, entity, plot, image or trade dress in the candidate |
| `gold` | gold labels missing or disagreeing with the rendered file |
| `audio` | speakers, turns, overlaps, noise, loudness |
| `file` | invisible file-level traits against the spec's File profile: PDF version, linearization, xref, metadata and XMP, fonts, image filters and PPI, JPEG internals (usually from `file_profile.py compare`) |
| `realism` | contextually inappropriate generation tells (placeholders, toy names, watermarks); implausible or inconsistent data; invented figures attributed to a real company or person (always `fatal`) |

## Severity

| severity | meaning | effect |
| --- | --- | --- |
| `fatal` | the fixture is unusable or unsafe: any leak, wrong format or unit count, gold that contradicts the file | score 0; never ships |
| `high` | an extractor would face a materially easier or different task: a difficulty feature lost, wrong table shape, missing block, wrong reading order | −15; blocks the pass |
| `medium` | noticeable contract deviation while the task remains the same: excessive density, column width off, caption short | −5 |
| `low` | cosmetic: font weight, small spacing differences | −1 |

`score.py` raises severities to these floors: `leak` → fatal, `gold` and `format` → high. A floor is a minimum, so the reviewer still marks a wrong container or unit count `fatal`. The score is 100 minus the penalties, or 0 when anything is fatal. The legacy rubric passes with no fatal/high misses and score ≥85; this is arithmetic, not a calibrated probability or automatic silver-label promotion.

Apply length penalties only when the frozen contract requires the measured length/density. The helper’s paraphrase ±15% band and 30% severity boundary are optional legacy defaults, not universal requirements. Run `overlap.py --no-length` when length is free. For different project tolerances, disable its length band and provide a separate contract-aware miss report; retain raw diagnostics. Do not feed an inapplicable legacy length failure into revision advice.

## Cause

- `spec`: the spec omitted the feature, described it wrongly or left it ambiguous. A better build cannot fix it.
- `build`: the spec was right and the Builder did not follow it.
- `unknown`: use it only when the cause can't be determined.

Getting the cause right matters. A checker defect is repaired and tested independently, then unchanged artifacts can be revalidated; do not classify a false positive as a required content rewrite. `score.py` supports only the three causes above, so keep tooling findings in a separate report until adjudicated. An uncontested high or fatal miss with demonstrated `cause: spec`, or an uncontested leak, calls for a spec rewrite. Duplicate occurrences incur one maximum-severity penalty while retaining each source report’s cause and original severity. A serious cause/severity disagreement requires diagnosis or adjudication before choosing a repair; report order must not choose the cause. Recurrence alone does not identify cause. Diagnose a repeated build failure against the correct contract, preserve the original cause/severity, and choose an adapter repair, different producer or bounded stop. Escalate to a spec rewrite only when an omitted, ambiguous or infeasible requirement is identified.

`diagnose` (exit 1) preserves reported cause/severity and adds recurrence flags and diagnosis notes for serious build/unknown repeats or a score below 50. It consumes the current round; it does not reset the budget. `rewrite-spec` requires a leak or explicit spec-caused high/fatal miss. Exhausted build rounds otherwise stop; low/medium recurrence alone remains threshold-eligible. Values beyond configured attempt/round limits are input errors (exit 2).

## Summary text

`summary` names the structure, length and role of the miss, and it never quotes the source. It goes to the Builder (after `overlap.py`) or into `spec_learnings`. Put any quote needed to justify the miss in `evidence`, which stays on the dirty side.

## Review scope and delivery

Keep audit and judge identities distinct. Record which pages/regions and dimensions were inspected, exact artifacts, method and limitations; disclose spot checks. Sampled visual review does not certify unseen content. Critical semantic or label contradictions block acceptance regardless of aesthetics.

Dirty-side reports may quote protected source content. Export only sanitized reports; never bundle restricted evidence with a clean fixture. Preserve raw lexical/tell failures and an occurrence-specific adjudication when they are false positives. Do not rewrite legitimate domain language to evade checks.
