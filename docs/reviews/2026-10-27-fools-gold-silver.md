# Fool’s Gold silver dataset skill revision

## Scope

This revision imports the existing local skill and improves its guidance, offline helpers and behavioral-evaluation assets. It does not accept the earlier mixed-PDF corpus, establish extraction thresholds or cost savings, or change production DocSlurp code.

The guidance draws on actual native-table, typeset-math, Office save/reload/export, raster composition and independent artifact reviews. The concise entrypoint routes to deeper production, corpus, verification, strategy and evaluation references. OpenAI and Anthropic primary guidance is linked in `skills/fools-gold-datasets/references/skill-evals.md`.

## Changes supported by the evidence

- Author meaningful quantities, units, assumptions, claim dependencies and references before rendering. Real tables and measured math layout replace plain-text grids and arbitrary algebra.
- Prove the smallest end-to-end producer path before expanding. Validate native editability separately from vector appearance, and bind exports to the reopened saved source.
- Separate source-free generation, source-blind stand-ins and permitted clones. Preserve source-sharing authorization, dirty-side reports and truthful producer history.
- Cross corpus factors, group derivative ancestry by split, and distinguish page share, raster area and compressed byte share.
- Diagnose the cause of repeated failures. Repair a checker against positive/negative controls without regenerating unchanged artifacts; change a contract only with evidence of a contract defect.
- Keep artifact, label, corpus and downstream-performance claims separate. Missing or unsupported evidence stays explicit.

## Independent reviews and resolution

Guidance, methods and adversarial reviews used separate Sol agents. The methods and adversarial checks used fixed Git source and invented controls, not restricted corpus inputs. Review findings are retained in the coordinator’s durable evidence store. Guidance R2 at `da08aa6` found no material guidance blockers or regressions; it did not assess changing code or artifacts. Code R2 independently replayed 103 tests and confirmed the original repairs. Its remaining ZIP/rubric findings were fixed in `4f13dff` and `651e36a`; independent methods and adversarial R3 reviews at `651e36a` found no blocking regression and reran all 115 tests. Methods retained a nonblocking ZIP bit-6 traceback variant. The coordinator fixed that at `fca13f6` by narrowly translating ZIP reader RuntimeError/NotImplementedError into structured refusals, with bit-5/bit-6 controls; that final follow-up was regression-tested but not independently re-reviewed.

Guidance R1 identified restricted-source provider-sharing authorization, unconditional legacy length penalties, recurrence misclassified as a spec defect, and a missing eval pointer. The revised guidance restores destination/retention scope, makes length bands contract-dependent, introduces diagnosis without cause/severity promotion, and supplies the behavioral assets.

Methods R1 identified unbounded evidence/arithmetic, same-context clean-output reads being rejected, unpublished interchange requirements, missing original-input bindings, missing pre-render semantic-label chronology, and malformed artifact exceptions. Adversarial R1 additionally identified DAG work amplification, hidden nested SVG text, incorrect TeX brace semantics, disconnected workflow ordering, malformed PNG filters, contradictory overlap metrics, malformed unsupported-format declarations, and undecoded Office metadata. Reproductions are retained as regression controls. R2 additionally found unsupported ZIP exceptions, reviewer-cause loss during deduplication, and contradictory failure strings misclassified as leaks. Required ZIP members now refuse unsupported compression/encryption before opening; duplicate penalties retain source-attributed reports and serious disagreements diagnose; contradictory failure messages are invalid input.

## Retrieval/Q&A extension

The dedicated retrieval reference separates real-question persona style from factual authority, grounds up to five facts in source page images, expands multi-retriever pools with reviewed duplicates and preserves negatives/unjudged states. It requires blind verification by a different model and separates retrieval, answer correctness, citations, abstention, realism AUC and difficulty. Stable page keys and connected family splits protect confirmation evidence. Three hand-authored routing contracts exercise activation and adjacent/adversarial requests; they are not behavioral results.

An independent guidance review at `a936524` found no concrete scoped findings and no private identity/data leakage. The user requested a generalized, standalone method rather than project-specific plan details. Recipe proportions and retrieval depths are chosen for the collection; optional aggregate targets are calibrated on development data before confirmation. No external plan is a prerequisite for row synthesis. No retrieval corpus, realism AUC or Q&A performance was measured by this revision.

## Two exploratory artifact trials

One no-skill and one revised-skill Sol/high trial received the same original two-page technical-report request and at most one repair. The baseline used Writer/ODT; the revised trial used ReportLab/Python/JSON. They authored different data, so this is not a controlled renderer comparison or a causal estimate of skill improvement.

An independent reviewer received neutral A/B copies of PDFs, page renders and labels without the arm map. All eight supplied artifact hashes and twelve residuals checked; both charts agreed and no critical clipping was found. It preferred the baseline’s explicit fictional framing. The revised report had richer labels and extractable vector-chart text, but its operational-use disposition lacked a stated acceptance criterion. The skill now requires disclosure placement and use criteria to be declared rather than silently inferred by a judge.

Native sources and full tool traces were absent from the blinded comparison, so that review did not establish native editability or process correctness. These two trials do not establish statistical improvement, human-calibrated judging, heldout transfer, or completion of the fourteen-task behavioral suite. First-build failures and reviewer preferences remain preserved. No direct model API or rented-compute workload ran; orchestration cost is unknown.

## Validation layers

Offline routing fixture results are hand-authored contract checks, not model behavior. Helper and artifact tests establish only their tested boundaries. The behavioral assets include fourteen public task briefs, a published output contract, separate grader criteria, synthetic setup, bounded offline grading and a future paired-trial recipe. Public challenge templates are not secret heldout instances. Mathematical numerical probes remain diagnostics requiring independent acceptance; the scorer always leaves agent skill performance unassessed.

## Executed checks

At final code checkpoint `fca13f6`, the coordinator ran **48 helper tests and 69 artifact-contract tests: all 117 passed**. Both suites include valid and invalid controls. Also passed: **21 Node eval tests**, **12 other helper tests**, **66 hand-authored routing fixture contracts**, metadata validation and local reference-link checks. The existing unrelated eval-expert host-policy warning remains disclosed by metadata validation.

Run the focused suites with `npm run fools-gold:test`; routing fixtures with `npm run eval`; metadata with `npm run eval:validate`. No full fourteen-task agent trial or transfer confirmation was run. The RAG extension added routing contracts and a procedure, not a measured retrieval corpus.

## Remaining limits

Collector custody and review identity require a trusted runner. Bounded parsers are small fixture profiles, not an isolation boundary or general file-format implementation. Rendered quality, semantic label correctness and real-world transfer still need the documented independent checks. Source-blind prompts on a shared filesystem do not enforce confidential access. This draft requires human merge approval; nothing deploys from this change.
