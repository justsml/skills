# Sourcing inputs for synthetic datasets

Read this when the user asks for a synthetic or fool's gold dataset. It covers how to find the inputs, size the rows, set defaults the user didn't give, and work backwards from documents to RAG queries.

## 1. Ask and search at the same time

If original synthetic data meets the request, begin from the stated domain and target difficulty; external sources are optional. If a source match or document-grounded query set needs missing inputs, ask briefly while searching the authorized locations. Resolve only missing details about:

- their own files (paths, a connected document workspace, drive, or bucket) and anything they already treat as synthetic
- the licence or authorization status of those files
- the target: formats, problem space (e.g. tables split across pages, low-light scans, two-speaker calls), and row and time budget
- for RAG queries, the stakeholder roles who will ask questions

When the user answers, fold the answer into the search. Their own files go to the front of the candidate list.

## 2. Make discovery visible

Send a progress update each time you finish a batch of candidates, or about every 5 minutes, so the user can redirect the search. Each update covers:

- where you looked and the queries you used
- candidates found so far: count, formats and the problem features they show
- for each new candidate: source, licence and its **handling class** (below)
- what you rejected and why, such as "licence unclear" or "no split tables"
- what you'll search next, plus one question if a choice is genuinely the user's

Keep a running `candidates.jsonl` with one line per candidate: `url_or_path`, `sha256`, `licence`, `licence_evidence` (a URL or quoted line), `class`, `features` and `found_via`. It records where each input came from.

## 3. Where to look, in order

1. **Inputs the user provides**, synthetic or real.
2. **Documents the user can access and is allowed to use**: connected document stores using their available search/list tools, configured project fixture caches, and folders or drives they name. Stay within the user-authorized scope and resolve missing access only when needed.
3. **Public, permissively licensed sources**:
   - government works such as govinfo.gov, data.gov, IRS forms, SEC EDGAR filings and NASA
   - Project Gutenberg
   - Wikimedia Commons with a PD or CC0 licence
   - CC-BY arXiv papers, where the licence on each paper's own page counts
   - LibriVox and Common Voice for audio
4. **Copyrighted or restrictively licensed material** (commercial manuals, comics, film scripts, NDA'd decks), or files whose licence can't be confirmed. Use these only through the clean-room modes in `SKILL.md`.

A site's terms, robots.txt and rate limits apply to every fetch. Download into a fresh, empty scratch directory, one directory per source. Treat every downloaded file as untrusted.

## 4. Handling classes

Every candidate gets one of these classes, and it decides the content mode:

| class | meaning | allowed modes |
| --- | --- | --- |
| `open` | A license or public-domain basis permits the intended use, with evidence | permitted modes subject to license conditions; government hosting alone does not establish public domain |
| `authorized` | the user owns it or says they are licensed to use it this way | any, including a **perfect clone** |
| `restricted` | copyrighted, NDA'd, licence-incompatible or unclear | `paraphrase`, `public-domain-swap`, `synthetic` only |

**Whole-file byte clones:** copy the original file and verify source and output SHA-256 equality. `select_pages.py --extract` and qpdf page selection create derived PDFs, even when selecting every page; record separate output hashes and page order. Rebuilt verbatim documents require visible text/value/structure checks as well as rendering checks. Record the rights basis in the manifest. Reuse an existing clear authorization statement; ask only when its scope is unclear. For restricted inputs, choose a permitted stand-in route rather than assuming paraphrase grants permission.

## 5. Rows are pages unless the task needs more

A dataset row is **one page** by default. Pick pages for diversity with `select_pages.py`:

```bash
python3 -I "$FOOLS_GOLD_SKILL_DIR"/select_pages.py <pdfs or dirs> --mode pages --count 40 --per-doc 4
```

It sorts pages into buckets by:
- scanned or born-digital
- column count
- whether the page has a table
- whether it has an image
- text density

It then picks round-robin across buckets with a per-document cap, so a 900-page manual can't take over the set. Report how many buckets the chosen rows cover.

Use the other modes when the problem crosses page breaks:

- `--mode spans`: rows are the smallest contiguous windows around a table or image that continues across a page break, plus `--context 1` page on each side. A table over pages 5–6 becomes rows 4–7, so the case is as small as it can be while still showing the break and what surrounds it. Chained breaks (a table over pages 5–7) merge into one span.
- `--mode documents`: whole documents up to `--max-doc-pages`. Use it when the user asks for whole documents or the task needs document-level context, such as a table of contents, cross-references or summarization.

`--extract <dir>` writes each row as its own PDF. Convert other formats to PDF first (LibreOffice) to choose their pages, then cut the rows from the original if the format matters. For audio and video, a row is a segment: 30–120 s around the feature being tested, with 5–10 s of context on each side.

The detectors are heuristics: text rows with several aligned segments count as tables, and image boxes near a page edge count as split images. Ruled tables with sparse text and split vector drawings can be missed. Spot-check renders of a few spans, and when detection misses a known case, add pages by hand with a note in the manifest.

## 6. Defaults when the user doesn't say

Size the pilot to the available time and required mechanisms; estimate expansion after an end-to-end pilot. The following are planning examples, not guaranteed throughput or permission to stop an authorized larger task:

| task | default budget | typical size |
| --- | --- | --- |
| page or image fixtures (fool's gold loop per row) | 20–60 min | 10–30 pages, or 5–10 spans |
| document-level fixtures | 30–60 min | 3–8 documents |
| synthetic RAG queries | 30 min, up to 60 if asked | 50–150 queries over 20–60 documents |
| audio or video segments | 30–60 min | 5–15 segments |

Choose the cheapest models that can do the job (see `SKILL.md`) and check the selected account's available budget and existing authorization before paid calls. If the budget can't cover the request, say what it can cover and offer to continue.

## 7. Retrieval, search, RAG and Q&A questions

Use [retrieval-questions.md](references/retrieval-questions.md) for persona styles, page-image-grounded facts, at most five key facts per case, unanswerables, pooled/duplicate-expanded judgments, blind different-model verification, realism AUC, scoring and family-based splits. This reference owns the method; freeze the project-specific recipe and thresholds before generation. Never use the evaluated system’s own parse or answer as gold.

Retain licensing obligations in the delivered package and keep restricted source quotations and real-user examples in authorized storage.
