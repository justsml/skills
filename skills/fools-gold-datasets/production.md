# Producing believable native artifacts

Choose a producer for the structure the task needs, then prove its actual export path. Reuse validated mechanics; keep authored content, layout and renderer adapters separate so changing a producer does not change the scientific facts.

## Select a capable path

| Requirement | Good starting point | Capability to verify |
| --- | --- | --- |
| Flowing technical PDF, equations, footnotes | Typst or LaTeX | Fonts, pagination, equation text/outline representation, tags if required |
| Precisely placed PDF forms, controlled geometry | ReportLab | Real `Table` layout, embedded fonts, clipping and reading order |
| Word/Writer-like document | DOCX/ODT via native document library and LibreOffice/Word export | Editable tables/equations, page styles, save/reload and actual PDF output |
| Web-origin PDF | Semantic HTML/CSS, MathML or typeset math, browser print | Pagination, table headers, font readiness and accessibility structure |
| Spreadsheet | openpyxl/XlsxWriter or native spreadsheet application | Typed cells, formulas plus recalculated cached values, merged ranges/charts |
| Slides | python-pptx/PptxGenJS or native presentation application | Native text/tables/charts and actual export behavior |
| EPUB | Semantic XHTML/CSS plus package metadata | Navigation, reading order and actual reader reflow |
| Charts/diagrams | Data-driven plotting; Graphviz/Mermaid/PlantUML for graphs | Plotted data versus printed labels; node/edge and caption ownership |

These are alternatives, not required installations. Preflight available versions/fonts with `check_deps.py`. Choose one default per needed path; switch after a demonstrated limitation rather than rewriting every library at once. A claimed producer must render the substantive document, not only a subtitle pasted into another tool’s PDF.

## Tables are structures

Use native cells, spans, row/column headers and repeated headers. In PDF-only generators, use a table layout object and retain its semantic cell map even though a PDF may not expose an editable table. Markdown is an acceptable label serialization; pipes, dash separators and tab-aligned prose are not a substitute for a real rendered table unless the source/task explicitly requires that representation.

Keep full units, qualifiers, signs, missing-value conventions and declared precision. Right-align numeric columns where useful; align decimals when supported. Resolve headers with deliberate wrapping and measured row height. A continuation may carry a long qualifier if the row link, reading order and cell ownership remain explicit. Never invent trailing zeros or filler to meet a character budget.

Measure ink and advance with the real font, both side paddings, border strokes and clearances. Check the longest header and widest signed value after export. A right-alignment property or an object getter is not evidence that the rendered columns align.

## Math has meaning, encoding and appearance

Retain all three:

1. **Meaning:** ordered expression tree, variable definitions, units, assumptions, sign conventions, precision, intervals and evaluated claims.
2. **Encoding:** LaTeX, Unicode, MathML or OfficeMath/OMML with a declared supported subset.
3. **Appearance:** typeset asset/native equation, measured bounds, baseline, scripts, fraction rules and font provenance.

Prefer full Typst/LaTeX for substantial technical documents; mathtext or another subset renderer is reasonable for supported expressions and plots. Use native Office equations when editability is required and proven. Vector embedding is a valid fallback for appearance, but disclose whether glyphs are text or outlines: outlined SVG does not establish searchability, accessibility or native equation editing. Never claim complete LaTeX support from a subset renderer.

Derive display forms from the semantic model where possible. Independently verify arithmetic, dimensions, rounding ties, interval bounds and claim dependencies. Keep descriptive statistics and screening comparisons separate from conformity or operational suitability; any disposition needs an authored use criterion, assumptions and decision rule. Standard fractions, ±, subscripts, superscripts, Greek and upright units are appropriate; do not degrade correct notation to ASCII solely to satisfy an old literal matcher.

Score correct supported encodings through a bounded parser/canonical structure, preserving case-sensitive identifiers, operand order, precedence, grouping, relation types and alphabet distinctions. Unsupported or ambiguous syntax is unscorable, not equivalent. Test positive cross-format controls alongside changed signs, swapped values, altered bounds, missing grouping and changed variable case. Encoding equivalence does not prove that an equation survives in its intended location or is visible; keep occurrence ownership and visible support as separate evidence.

Measure asset ascent/descent and neighboring labels before placement. Validate embedding in the actual target producer: save/reload can change SVG behavior. Subset/deduplicate fonts when supported; a full font repeated inside every equation can dominate PDF bytes and distort extraction-cost experiments. Preserve actual byte costs if deduplication is unavailable.

For math-heavy fixtures or custom math scorers, read [Math and export regression lessons](references/math-and-export-regressions.md). It records concrete cross-encoding, rendering and evidence failures that ordinary happy-path checks missed.

## Figures and screenshot insets

Plot charts from authored data; retain printed title, axes, legend and ticks separately from underlying series. Native Office charts and raster screenshots are distinct extraction cases. Use diagrams with meaningful relationships, not decorative generic pictures.

Create a separate original document for a screenshot inset, then crop/render it. Store its source identity, visible region, text and relationship to surrounding commentary. Ensure the commentary makes a meaningful comparison, interpretation or decision. A bitmap of random text or a paragraph merely saying “see figure” contributes little realistic difficulty.

Use code for exact charts, tables and diagrams. Use an image model or licensed image only when illustration/photo realism benefits and authorization permits it. Keep exact textual labels outside generated bitmap art where correctness is required. Restricted source art is not an input to tracing, restyling or image generation.

## Native export and persistence

Treat the file opened after saving as the input to export:

`author → save → close → hash native file → reopen → inspect native state → export → verify native hash unchanged`

Record the exporter/version/options, input hash, output hash and process outcome. A hash measured only after export does not prove which native file was exported. Inspect actual table XML/cells, spans and math representation as appropriate.

Give concurrent Office jobs isolated user profiles, ports, work directories and output names; bound concurrency empirically. Stop only owned processes. Avoid a single shared mutable document controlled by multiple agents.

When an API getter changes after reload, preserve both raw values. Compare saved structure and independently measured rendering to determine whether the artifact changed. An explanation such as “internal sentinel” is a hypothesis until supported. Unsupported states should narrow a validator’s claim, not trigger endless document rebuilds.

## Scan, image and file variants

Render clean accepted references first, then apply reproducible degradation: DPI, resampling, blur, contrast, skew, noise, compression and masks. Use plausible correlated capture conditions rather than independent extreme sliders everywhere. Keep a few controlled extremes as named stress cases.

Differentiate native text, text outlines, embedded screenshots, partial raster regions and image-only scans. Ensure native text is actually removed where intended. Retain source-to-display coordinate mappings, integer raster dimensions, page indices and crop/rotation metadata. Compare untouched regions and actual transformed output, not flags set by the generator.

Use `qpdf` for supported container/storage rewrites and inspect its resulting profile. A Ghostscript re-distill may change visible content, fonts or images; it is not automatically storage-only. `pdf_variants.py` offers presets, but each selected preset needs content and render checks. Do not falsify Producer/Creator to pretend an engine ran. Metadata perturbation is permitted as an explicit experimental factor with true history retained.

## Other media

For audio, preserve a script with speaker/turn IDs, timing and overlap before synthesis. Use available TTS voices/engines, mix measured room/noise conditions with ffmpeg/sox, and inspect intelligibility, prosody, disfluencies and boundaries. Clean TTS with added noise is not representative of all real speech. Timed authored text remains unverified until checked against the waveform.

For video, retain scene/onscreen-text timelines, source frames, audio references and mux settings. Use data-driven slides/animation where appropriate; check frame timing, captions and audio alignment after encoding. Codec/container success does not establish audiovisual fidelity.

## Inspect and diagnose

Show full pages plus readable close-ups of dense tables, equations, insets and hard scans. Use more than one renderer/parser when their disagreement would expose a risk. Preserve reference overlays and failures; do not promote a contact sheet as exhaustive inspection.

Differentiate observations at finite raster/trace precision from exact glyph conservation. Validate clipping, transformations and font assumptions with counterexamples. For normal silver data, practical rendered inspection with a stated scope is useful; a formal visibility proof is not a prerequisite unless the downstream claim requires it.

Natural documents may contain ordinary software metadata and words such as “sample,” “control,” or “synthetic biology.” Keep `check_tells.py` flags for contextual review. Avoid obvious filler or invented claims about real entities. Use plausible purpose-specific data rather than forcing all numbers to be non-round or all dates to be business days.
