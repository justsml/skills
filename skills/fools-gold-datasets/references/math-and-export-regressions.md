# Math and export regression lessons

These lessons come from a mixed native/raster technical-PDF build and scorer review on 2026-10-27. They describe demonstrated failure classes, not a certified parser or a requirement to reproduce that project's architecture. Apply the controls relevant to the intended claim.

## Build meaningful technical content first

Start with a coherent domain, quantities and decisions. Equations should explain an actual relationship, such as a discharge rate, weighted temperature or calibration residual. Preserve definitions, units, assumptions, sign conventions and rounding ties visibly in the document. Random noun substitutions in algebra produce superficially technical pages without realistic reasoning or extraction demands.

Keep formula definitions, evaluations, table values and claim dependencies in an authored model. Give supplementary definitions and results their own owned child blocks and reading order. A mathematically correct world JSON does not repair a missing qualification on the rendered page. Independently recompute values and check that the printed interpretation follows from them.

Prove a representative full page early, then a multipage export, before authoring a large corpus around an unproved layout. Character-count budgets can contradict legitimate signs, units, headers or inherited literals. Resolve the exact conflict with measured ink bounds and an explicit contract revision; retain the old diagnostic. Preserve precision rather than padding values with zeros or dropping qualifiers to satisfy counts.

## Rendering and export controls

- Real tables need cell geometry, padding, spans and alignment in the native producer. A Markdown gold table is a serialization of those cells, not the page's rendering implementation.
- Measure actual math at its intended nominal size, including script extents, fraction bars, neighboring labels and table padding. A beautiful enlarged standalone equation does not prove fit in the original page slot.
- Derive the next block's position from the preceding asset's measured height. Fixed coordinates caused typeset fractions to collide with tolerance labels even though every asset rendered correctly in isolation.
- Test outlined math separately from text math. Outlined vector SVG can preserve appearance through Writer export while losing equation editing, search and copy semantics. Record that representation honestly.
- Inspect the exported document and the saved native source. A real editable table and a vector equation pasted beside it establish different capabilities.
- Preserve export-time native hashes. A post-export hash alone cannot establish what was reopened and converted. Save/close/hash/reopen/export/unchanged-input checks should identify the same native artifact.
- Keep raw persistence readbacks when getters disagree with saved XML or rendering. Adjudicate the discrepancy with independent geometry; do not rename an unexplained mismatch a pass.
- Font payload matters in byte experiments: repeated full fonts in per-equation SVGs can dwarf the actual content. Inspect final embedded resources and account for them, rather than assuming a vector asset is small.

## Cross-encoding equivalence controls

Normalize a declared supported subset to an ordered, case-sensitive expression structure. Correct LaTeX, Unicode, presentation MathML and Office Math Markup Language (**OMML**) may encode the same expression differently. Preserve unsupported input as unscorable; do not turn it into a perfect score, discard it from an aggregate, or penalize it as a proven wrong answer. Encoding equivalence is distinct from general algebraic equivalence and domain-dependent simplification.

Use a matrix of equivalent encodings plus meaning-changing controls. Include these demonstrated pitfalls:

| Failure | Required distinction or control |
| --- | --- |
| Nested scripts flattened into sibling scripts | `(x^n)_i` differs from `x_i^n`; linear sibling forms `x_i^n` and `x^n_i` may agree. Exercise nested MathML and OMML structures too. |
| Baseline XML text treated as TeX markup | A caret, underscore or superscript character inside a baseline XML run must not silently acquire structural script meaning. Use the XML structure or refuse an ambiguous form. |
| Office Math run fragmentation changes meaning | Joined and compatibly split numbers/identifiers should agree. Empty runs, including empty runs with another style, must not insert multiplication. Nonempty style changes still need deliberate handling. |
| Mathematical alphabets folded together | Preserve supported bold, normal, italic and double-struck distinctions. Refuse an unrepresented combined style rather than silently dropping it. U+2145–U+2149 are double-struck italic letters. |
| Unicode modifier mapped to the wrong base | U+1DA6 `ᶦ` is small-capital I, based on `ɪ`; U+2071 `ⁱ` is lowercase i. Audit hand-written script maps against character identity rather than visual resemblance. |
| MathML inheritance only partly honored | Check direct and inherited styles on `mi`, `mtext`, **`mn` and `mo`**, including fraction children and exponents. Accepted styles must survive normalization or be explicitly unsupported. |
| Relation chains parsed as arithmetic binaries | `p<q<r` must not normalize identically to `(p<q)<r`. Represent chains distinctly or refuse the unsupported forms; cover mixed relations and XML encodings. |
| Correct substring credited inside a longer formula | `q=a/b` differs from `q=a/b+c`. Match complete expressions, preserving operators, grouping, case and relation type. |

Harmless envelopes also need positive controls: ordinary whitespace, supported Markdown headings around math, one permitted decoded XML declaration, and supported OMML paragraph alignment. Preserve mathematical line-leading minus and multiplication signs when normalizing Markdown.

## Bound the actual parser path

Length, token, tree-node and depth limits protect different resources. Exercise them in the supported runtime rather than inferring enforcement from a constant in source.

Reject invalid decoded XML characters before parsing. NUL-interleaved strings can make a parser infer a byte encoding while bypassing textual declaration checks. A valid already-decoded XML declaration is a separate supported-envelope decision; it does not justify accepting malformed decoded strings. Refuse DTDs, entities and unknown structures within the restricted profile, and verify that parsing performs no input-driven file or network access.

Pull-parser events can be deferred until `close()`, particularly after a long whitespace-padded start tag. Apply the same root discovery, node counting and depth validation to feed-time and close-time events. Include padded valid roots, padded depth overflow and padded node overflow as controls. If the claim is early allocation prevention, counting after a complete tree has been allocated is insufficient: use bounded construction or a parser target that enforces the relevant bound while building. An input-length cap remains useful but does not prove the other limits.

## Equivalent expressions do not establish preserved occurrences

A correct quotation can conceal a corrupt operative formula. Global token coverage, short context windows, occurrence counts and even uniquely forced sequence alignment all produced false acceptance when the extraction deleted or changed a declared equation and inserted a compensating copy elsewhere. Include deletion-plus-duplication, recased original context and inserted quotations as negative controls.

Keep four claims separate:

1. The two supplied expressions have the same supported structure.
2. The candidate expression belongs to the declared source occurrence.
3. Candidate text, raw words, regions and renders describe the same frozen artifact.
4. The expression is visibly present and legible in the delivered page.

An expression-only scorer can establish the first within its supported subset. It cannot promote the other three. Raw boxes alone can credit hidden correct text over visibly wrong mathematics; a tight region can omit a changed operator outside it. Visibility-sensitive acceptance needs complete region inventory, provenance, candidate-span ownership and independent visible support, with ambiguous cases incomplete or adjudicated.

## Geometry and evidence controls

Recompute clipping from bounds instead of trusting a supplied `clippedByDisplay` flag. Require integer raster dimensions and correct page ownership in OCR rows; reject unknown/truncated rows and unexpected fields. Rotation and crop must use one explicit coordinate basis, including raster-rounding effects.

An outline checker needs controls for text horizontal scaling, signed rectangle extents, deferred PDF clipping paths, rotation and unsupported transforms. A clip operator whose path is completed later can defeat a checker that assumes immediate termination. A valid negative-height rectangle is not automatically malformed. Refuse unsupported states without awarding complete coverage.

Trace coordinates have finite precision. “No excursion detected at reported precision” does not establish exact glyph conservation; retain that distinction instead of inventing a global error tolerance from one successful sample. Ordinary silver-fixture review can use practical visual evidence with stated limits, while downstream exactness claims require stronger support.

## Review and promotion discipline

Bind each audit, judge decision and semantic receipt to the exact corpus, labels, spec, validator version and per-case outcomes. Require distinct review-stage identities and link each score decision to its actual report. Validate evidence paths, including resolved symlinks, before opening or hashing them when protected labels are out of scope.

For frozen checker execution, run the verified byte buffer or another immutable verified artifact. Hashing a mutable path before and after execution permits replace-and-restore races. A digest establishes identity only for the bytes actually checked.

Review fixes with both the original counterexample and nearby variants. Run the actual scorer adapter as well as pure helper tests; successful mocked integration is narrower evidence. A review with passing prior controls can still find new defects, so report unresolved findings rather than treating accumulated test counts as acceptance.

At the end of the source session, the first six math-normalizer repairs passed independent controls, but relation chains, small-capital mapping, inherited numeric styles, empty Office Math runs and deferred XML limit accounting still had open findings or fixes in progress. Formula occurrence/visibility promotion remained closed. The complete mixed corpus, held-out thresholds and cost savings were not established. Preserve that scope when reusing these lessons; do not import prototype or test counts as a new project's acceptance result.
