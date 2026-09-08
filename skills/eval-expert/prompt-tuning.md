# Tune a prompt against evidence

Read this when the editable component is a prompt and the loop has stalled: a model swap regressed results, gains flattened, or one failure cluster will not move. Each strategy below is an instance of the search loop in [`phases/optimize.md`](phases/optimize.md) — hypothesis, bounded change, paired evaluation against baseline, keep or discard from evidence. A strategy that sounds principled but does not move the development score is still a discard.

Two rules apply throughout. Score every variant on the same development cases as the baseline, and never on held-out data. And read [the cost guards](cost-guards.md) before starting — these strategies multiply runs.

## First: check the model card, then verify it

Look up the target model's official model card and prompting guidance before hand-tuning around unconfirmed folklore — stated preferences for markup, system-versus-user placement, tool-call conventions, known quirks.

Treat every claim as a hypothesis to test on the development set, not a fact. Provider guidance can be stale, generic, or wrong for this task. One A/B per claim, kept only if it measurably wins.

## Strategy 1 — clean slate, then accrete

Use when the prompt has grown by accumulation and nobody has re-justified its older sections.

1. Set the current prompt aside. Do not edit it.
2. Write three or four genuinely different prompts from scratch — different framing, different structure, not variations on the incumbent.
3. Score each on the development set. Keep the strongest as the new base even when it looks sparser than the original, and even when it loses to the incumbent — record that gap as the budget the next step has to close.
4. Add instruction chunks back one at a time. Each chunk targets a specific failing row or cluster.
5. Keep a chunk only when it measurably fixes what it targeted. Discard the rest, including chunks that feel obviously necessary.

Stop when added chunks stop paying for themselves, or the reconstructed prompt beats the incumbent and further chunks are flat.

## Strategy 2 — vary markup and register

Use when the content looks right but the model applies it inconsistently, especially after a model swap.

Hold the content fixed and vary only its packaging, one axis at a time:

- Markdown headings vs. XML tags vs. a mix.
- Dense structured lists vs. human prose.
- Rules-and-requirements framing vs. worked examples.

Different models respond differently to the same instructions in different clothing. This is a real axis to search, not cosmetics. Stop once one packaging wins outside measurement noise, or all packagings land within it — in which case packaging is not the constraint and you should move to Strategy 3.

## Strategy 3 — slice for load-bearing content

Use when you need to know which parts of the prompt are doing the work before spending more effort on any of them.

1. Ablate section by section — or statement by statement for a short prompt. Drop one, score the development set, restore it.
2. Record each section's delta. That delta is what the section carries.
3. Cut sections whose delta is zero or negative.
4. Route your remaining effort by the deltas, not by how important a section looks.

The routing rule is the point. A **load-bearing** section with a large delta has little room left — its residual failures are usually caused by something else, so tuning it further mostly wastes runs. A **marginal** section with a small positive delta is where outsized gains hide, because a small under-tuned part can carry disproportionate improvement once corrected. Do not spend equal effort on both ends of that spectrum.
