# Corpus design and controlled difficulty

Read for datasets, splits and variants. A thousand encodings of one page remain one content family.

## Define the population before expanding

Start with the intended downstream capability and a coverage matrix: genre, content complexity, layout, producer, representation, language/script, length and degradation. Include easy native controls, realistic common cases, mixed pages and rare hard cases. “Hard” must name an observable property or a measured failure—not just a large file.

Cross factors independently where practical. Assigning layout with `family % 3` and raster share with `family % 6` confounds them. Use a balanced factorial pilot for important interactions; use stratified or pairwise coverage when a full factorial is too expensive. Publish the actual cell counts and missing combinations. Preserve a natural-prevalence set separately from a stress set.

Plan source-family diversity before multiplying encodings. Vary author intent, rhetorical structure, data relationships and cross-page dependencies. Keep notation reuse separate from prose reuse. Use lexical/semantic duplicate screening as flags, then inspect; neither a low overlap score nor random names proves novelty.

## Split by ancestry

Assign training, development/tuning and held-out confirmation at the root-family level before optimization. Group all pages, reordered/subset copies, screenshots, producer variants, translations, paraphrases, related world derivatives and queries with shared answers into the same split. For multi-document questions, group the connected source families together.

Check declared ancestry **and** observed identities: original/native/delivered byte hashes share one namespace; canonical page content and asset identities detect renamed or reordered copies. Review near-duplicates across splits. Hashes catch exact reuse, not all semantic leakage.

Freeze expected inventory, split membership, ordered page IDs and versioned references. Reject missing/extra/duplicate cases and cross-split reuse before opening held-out labels or predictions. A complete file that merely lists existing successes does not establish completion of the planned panel. Bind the selected policy and scorer to the exact inventory before confirmation. A changed policy needs new untouched evidence, not retuning on the old holdout.

## Distinguish raster measures

Record separately:

- Fraction/count of image-only hard pages in each document.
- Fraction of page area covered by images (union of placements, not summed overlap).
- Fraction of authored regions or visible text rasterized.
- Unique compressed image stream bytes, mask bytes, decoded bytes and total file bytes.
- Requested and realized degradation: DPI, blur, contrast, skew, JPEG quality, color mode and seed.

A file with 20% scanned pages need not have 20% image bytes or 20% raster area. Use explicit denominators. Keep screenshots that contain relevant text separate from decorative photos; label both their content and the commentary interpreting it. For hard scans, verify that no selectable native text survives beneath the rendered page. Do not equate unreadable synthetic corruption with realistic OCR difficulty.

## Transform recipes and invariants

Freeze the clean base and authored references first. Record each operation’s input/output identities, selected region IDs, page geometry and coordinate transform. Only mark outlines/rotations/masks applied when actually emitted.

Useful controls:

- Storage rewrite: visible rendering and semantic content invariant, structural profile changes as intended.
- Native → region raster: targeted native text removed, outside content invariant, gold preserved within the declared readability scope.
- Rotation/crop: coordinates and image coverage agree in a common display space.
- Shared font/image/mask: object streams counted once physically; indirect page ownership retained.
- Degradation: labels remain visible/readable or are explicitly uncertain/abstain; record both intended clean text and observable target if the task needs both.

Do not compose unsupported transforms silently. Test overlapping operations, clipping and font cases independently before expanding their combinations.

## Measure useful downstream difficulty

After fixture validation, compare a small panel of independent extractors to understand challenge coverage. Use development data for selecting gaps, not held-out labels. A generator that only exploits one parser’s bugs is not a representative corpus.

Byte residuals after image subtraction are features, not expected text bytes: fonts, vectors, shared resources, metadata, compression and container overhead remain. `pdfimages` output bytes may differ from compressed embedded streams. Single-page/chunk rewrites duplicate shared resources; equal division of four-page residuals is an allocation heuristic. Record object-accounting errors explicitly instead of treating them as zero.

Benchmark equivalent work with fresh, randomized, repeated runs. Separate rendering/probing, layout extraction, coordinate capture, split overhead and total document latency. Historical cache times are not fresh timings. Include fixed baselines in policy selection and quality/acceptance constraints on important hard slices. Report paired family uncertainty and actual service costs; local elapsed work alone does not establish hosted-dollar savings.
