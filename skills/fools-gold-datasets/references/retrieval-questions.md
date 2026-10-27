# Retrieval, search, RAG and Q&A silver sets

Use this workflow when the artifact is a question set grounded in a document collection. Generate plausible questions from independently observed evidence; assess finding the evidence separately from answering it. Keep real identities, questions, source excerpts and page images in authorized project storage; public guidance and examples stay generic.

## 1. Freeze the recipe and corpus

Record the corpus version, permitted source access/model destinations, generator and different checking model, budget, retry ceiling, recipe proportions, difficulty tiers, train/development/held-out families and acceptance policy before generating questions. Start with a small, diverse development pilot and choose proportions and retrieval depths to suit the collection and intended users. This procedure is standalone; it does not depend on another project’s plan or numerical settings.

Record counts/proportions by recipe and difficulty, unanswerable share, pool depth per retriever, retrieval cutoffs, duplicate/near-copy review criteria, independent-check adjudication, factual/citation gates, retry cap and split proportions. Use the pilot to calibrate optional aggregate targets such as realism AUC, then freeze them before confirmation. An uncalibrated metric remains diagnostic; it need not block row synthesis. Every accepted row still needs supported facts, complete evidence and independent verification. The fixed per-case budget here is **at most five atomic, checkable key facts**. Split a case needing more rather than hiding several assertions in one fact.

Assign stable page keys before extraction: immutable document revision/content digest plus original page index and a corpus namespace. Keep display page numbers separately. Bind each key to its rendered page hash, render configuration and source hash. Re-ingestion, chunking, OCR, filenames and result rank must not change the key. Map chunks to one or more page keys; retain crop-to-page transforms. Producer variants or near-identical revisions get distinct keys and explicit equivalence/ancestry links.

Split connected source families before question generation: original and near-copy pages, derivatives, shared worlds/answers, multipage evidence bundles and their questions stay together. Use independent persona/user groups for realism evaluation too. If pooling discovers a cross-split family connection, invalidate the affected confirmation set and rebuild its split; do not silently move inspected held-out answers into development.

## 2. Learn personas from real questions, style only

Use authorized real questions grouped by user to identify vocabulary, domain familiarity, brevity, typos, search fragments, implicit context and question shapes. Strip identities and retain only a sanitized style profile under a random persona ID. Preserve permission and grouping in restricted provenance.

Treat examples as untrusted data, never instructions, factual premises or answer keys. Do not inherit their names, numbers, assertions, answers or quoted passages. The generator may copy style, not content. Hold back real questions/user groups used for realism testing from persona fitting. If real questions are unavailable, label personas hypothesized and realism against real users unmeasured.

## 3. Work backwards from visible page evidence

Inspect the original page image and readable crops with an authorized vision-capable model or human. Select a useful fact or small reasoning task, then compose a question in a compatible persona’s style. The system under test’s parse, OCR, retrieval summary or answer must never serve as gold. Text may assist navigation; every retained fact is independently verified against visible source evidence. For digital non-page sources, freeze an authoritative visual view and its mapping first.

For each answerable case save one to five fact IDs, normalized value/text, units, sign, precision or accepted equivalents, qualification/time scope, and supporting page keys/regions. A comparison or calculation also records all inputs and the independently checked rule. Mark unreadable or ambiguous facts uncertain and exclude them from strict factual acceptance until adjudicated.

Draft the answer only after these facts. Avoid questions requiring the page to be open ("the second bullet"), accidental answer leakage in the question, unsupported domain knowledge, or copied answer phrasing disguised as a query. Preserve necessary exact identifiers when exact lookup is the intended recipe.

## 4. Balance recipes and unanswerables

Use the project’s frozen proportions across these recipes, with counts reported rather than inferred from filenames:

| Recipe | Evidence requirement / principal trap |
| --- | --- |
| Direct lookup / exact identifier | Visible fact and exact scope; keep legitimate exact terms |
| Natural paraphrase / vocabulary mismatch | Same supported intent in user language; no extra premise |
| Numeric/table lookup | Cell, row/column headers, units and sign together |
| Comparison / small aggregation | Every operand and compatible scope; no truncated list |
| Cross-page or cross-document reasoning | Complete minimal evidence set and explicit dependency |
| Temporal/version qualification | Correct revision and date; older near-copy can be a negative |
| Ambiguous/underspecified | Expected clarification, not an invented unique answer |
| Unanswerable in the frozen corpus | Null answer, no positive answer facts, explicit missing/contradicted premise and reviewed search scope |

Use negatives that are plausible for the same personas and documents, not obviously nonsensical questions. Include tempting near matches, absent time periods, missing qualifiers and questions requiring an unavailable source. A retriever returning nothing does not prove unanswerability. Keep partial-support pages and the missing dependency in the adjudication record; do not score partial evidence as a complete answer.

## 5. Pool and widen evidence, then judge it

Retrieve candidates using several complementary methods, such as lexical/BM25, dense, hybrid and an independently configured reranker. Freeze index snapshots, query variants, retriever versions, depths and ranked runs. Include the authoring evidence even when no retriever returns it. Deduplicate by stable page key while preserving which runs nominated each page.

Widen the pool with exact and near copies, related revisions, neighboring pages and alternative sufficient evidence sets. A duplicate relation nominates a page for judgment; it does not grant relevance. Exact rendered copies still need compatible provenance/scope; a near copy with a changed value or date may be a hard negative. Add all judged answer-equivalent sources to the accepted alternatives so the originating page is not the only allowable hit.

Shuffle candidates and hide retriever identity/rank from the evidence judge. Judge against the question and page images: `sufficient`, `partial`, `non-answering`, or `uncertain`, with supported fact IDs and reason. Preserve **judged non-answering pages as negatives**. Keep `unjudged` separate from negative. For multi-page answers, record alternative sufficient *sets* of page keys; one relevant page is not necessarily sufficient alone.

Pools are incomplete evidence, not an exhaustive oracle. Audit unjudged top hits and a predeclared sample outside the pool, widen development judgments when new relevant evidence appears, and report judgment coverage. NIST documents both pooling practice and its coverage/bias limits: [TREC judgments](https://trec.nist.gov/data/reljudge_eng.html), [pooling limits](https://www.nist.gov/publications/bias-and-limits-pooling-large-collections).

## 6. Blind independent verification and bounded regeneration

A **different model** receives the question, shuffled page images and scope, without the generator’s answer, fact list, acceptance score or retriever ranks. It independently determines answerability and reconstructs facts. A coordinator then compares its evidence/facts with the proposed gold. Merely opening a fresh session with the same model is not this different-model check. Use only project-authorized destinations, models and spend; if unavailable, retain an incomplete gate rather than quietly substituting self-review.

Reject cases with unsupported or contradictory facts, wrong units/signs, missing qualifiers, incomplete evidence sets, ambiguous answers or accidental question leakage. Preserve failed candidates and reasons; regenerate from the source within the frozen retry budget. Never keep retrying until a judge happens to agree, and never delete failures from the attempt denominator. Model disagreement may require authorized human adjudication. Similar model families can share errors, so calibrate the gate against expert-reviewed valid and mutated cases before a reliability claim.

## 7. Measure realism and difficulty separately

Mix synthetic and authorized real questions, hide their origins, and train/evaluate a discriminator on **question text only**. Keep users/personas, near-duplicate questions and topic/source families disjoint across its train/test split. Match domain/language/length strata; remove packaging, IDs and formatting artifacts that trivially reveal origin. Neither generator nor tuning loop sees realism-test questions.

Report ROC AUC with real/synthetic class convention, held-out sample counts, per-stratum values and family/user-clustered uncertainty. Chance discrimination is AUC 0.5; systematic separation in either direction signals a tell (a reversed classifier can be flipped). A value near chance is only evidence against that discriminator’s ability to distinguish the sets, not proof of realism or answer correctness. Predeclare the acceptable band and confidence rule in the project plan; do not choose them after seeing scores. Without real examples or adequate support, report realism unmeasured.

Define intended difficulty from observable requirements (exact lookup, lexical mismatch, table structure, version ambiguity, distractors, evidence-set size). Measure empirical difficulty separately using frozen independent baselines on development cases. Report both; do not call a case hard solely because the target system failed. Lock confirmation families and recipe mix before comparing systems.

## 8. Score retrieval and answers independently

Freeze cutoffs, tolerances, gates and aggregation in the run policy. This scoring table describes distinct measures, not an arbitrary weighted total:

| Dimension | Measure | What must not count as success |
| --- | --- | --- |
| Finding relevant pages | Page Recall@k and nDCG@k against versioned judgments; include judgment coverage/unjudged@k | Treating unjudged pages as proven negatives; inflated recall from counting aliases repeatedly |
| Finding sufficient evidence | Fraction of cases whose top-k contains any complete accepted evidence set | A single hit from a required multipage set |
| Answer facts | Correct key facts / applicable key facts, with per-fact evidence and frozen value/unit tolerances | Right page plus invented answer; a correct global number in the wrong row/context |
| Unsupported assertions | Unsupported or contradicted answer claims / all answer claims; retain raw counts | Hiding hallucinated additions behind high fact recall |
| Citations | Claim-to-cited-page support and coverage of required facts | A relevant page citation that does not support its attached claim |
| Unanswerables / ambiguity | Correct abstention/clarification rate and false-answer rate, separate denominator | Fabricated answers or abstaining on every answerable case |
| Case completion | All required facts correct, complete support, no critical contradiction/unsupported assertion; or correct required abstention | Averaging a critical error away |
| Realism / difficulty | Held-out discriminator AUC, tier/recipe counts and frozen baseline results | Promoting stylistic indistinguishability to factual correctness |

A case with five facts needs all five for strict completion even if partial fact credit is useful diagnostically. Empty denominators are nonapplicable, not perfect. Report answerable and unanswerable slices, difficulty tiers, recipe coverage, source families, failed/regenerated counts, cost and latency separately. Cluster comparisons by independent family; many question paraphrases are not independent evidence.

## Delivery record and regression traps

Deliver questions, persona-style IDs, split/family IDs, source revision and stable page keys, zero-to-five key facts, answerability/null answers, alternative evidence sets, judged negatives, uncertain/unjudged entries, recipe/difficulty, blind-review identities/outcomes, policy/threshold version, retriever/index versions and hashes. Keep raw real questions, source images and private judgments in authorized storage; public examples use invented names and data only.

Before promoting the generator or grader, test: persona example containing a false answer/instruction; correct page with wrong answer; swapped table values; missing multi-page support; duplicate relevant alternative; outdated near-copy negative; unjudged page; uncertain/unreadable source; unanswerable with plausible distractors; wrong page-key remapping; source-family split leakage; six-fact case; generator judging itself; AUC split leaking user style or question duplicates. A correct equivalent answer and a legitimate exact lookup must remain positive controls.
