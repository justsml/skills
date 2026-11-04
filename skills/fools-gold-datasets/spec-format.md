# A buildable fixture contract

Use a compact spec for a small fixture; a structured companion becomes useful for many pages or transformations. The contract must be feasible, not merely precise. The Builder should be able to explain what is fixed, what can vary, and how completion will be checked.

## Scope and authority

Record content mode, rights basis, target use, formats, page/segment count, physical size, audience, genre and intended challenge. Separate required features from stylistic preferences. Give each constraint an origin (user requirement, measured source feature, experimental factor, or design choice). Record conflicts and chosen resolution before rendering; do not silently discard inherited requirements.

For restricted-source stand-ins, transmit roles, abstract relationships, geometry and measured density—not source wording, identifying plot/image descriptions or raw metadata. Sanitization covers specs, notes, filenames, logs and profiles. A denylist may itself reveal source names: keep it with the source-side checker, not in the Builder handoff. Automated overlap checks supplement a source-aware handoff review.

## Semantic authoring model

Author a small domain model before display strings:

- Stable document/page/block IDs and explicit ordered children.
- Facts: entities, timeline, quantities, units, exact or rounded values, precision and rounding/tie rules.
- Tables: typed row/column/cell IDs, headers, spans, units, missingness conventions and footnote ownership.
- Equations: meaning, variables, assumptions, expression tree, evaluation inputs/results, display LaTeX/MathML/OMML and relation type. A scalar result alone does not identify the intended expression.
- Charts: plotted series, units, axes, legends and printed ticks distinct from latent numeric values.
- Claims: IDs of supporting cells, equations, observations and explicit limits. Include population, interval and sign conventions where they change interpretation.
- Insets: independently authored source document, crop/page reference, visible text, and separate surrounding commentary.

Write useful narrative from the model: purpose → method → evidence → interpretation → limits/action. A collection of invented terms joined by arithmetic is not a technical document. Repeated templates can share notation; vary the situation, evidence, reasoning and outcome.

## Layout model

For each block, record role, page, reading order, parent/children, bounding box, coordinate origin/units, rotation, z-order and allowed reflow. For transformed outputs also retain page media/crop boxes, display rotation and raster dimensions.

Use budgets appropriate to content:

| Content | Prefer |
| --- | --- |
| Prose | Measured line capacity, readable font/leading and approximate word range |
| Numeric cells | Type, precision, sign, unit and measured width; no artificial minimum character count |
| Header/caption | Measured wrapping and row height, with units bound to the label |
| Math | Actual typesetter bounding box, ascent/descent, scripts and clearances |
| Footnotes/qualifiers | Explicit owner, full wording, continuation location and reading order |

For matched sources, retain measured block geometry and per-block errors, not only mean IoU. Set tolerances according to the feature being preserved; 0.70 IoU or a pixel percentage is not a universal quality law. Original documents may reflow where the user has not fixed geometry.

Measure with actual cell padding on **both** sides, font ink overhang and stroke extents. Advance width alone is insufficient. Give numerical values with explicit units and evidence for any reserve; do not generalize one producer’s margin constant to all outputs.

## Difficulty and production contract

Declare native producer/version and required editable structures; fonts and permitted substitutes; native/outlined/raster representations; images/masks; occlusion; hidden text; rotation; scan parameters and intended readability range. Separate deliberately difficult artifacts from broken generation.

Declare required, forbidden and free file-profile traits. All source strings, including Creator/Producer, font and image metadata, are restricted-side input until sanitized. Treat actual producer history as provenance; alternate metadata is a separate declared test factor. PDF/A or accessibility claims require corresponding validation.

## Feasibility and freeze

Before full authoring, demonstrate the longest header, widest numeric value, most complex equation, densest body and, for multipage work, a page break through the intended producer. If the combination cannot fit, propose a minimal measured correction with affected constraints and unchanged semantic facts. Avoid tiny fonts, truncated qualifiers, fake precision or arbitrary prose padding.

Freeze the selected contract and original references before rendering. Freeze rendered geometry separately once observed. Do not pretend planned boxes were measured output boxes. Assign output page IDs explicitly and validate order, count and source ancestry before scoring.
