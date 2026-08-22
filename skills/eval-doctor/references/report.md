# Eval doctor report

Write a single HTML file named `<tmpdir>/eval-doctor-<repo>-<timestamp>.html`. Resolve the OS temporary directory from `$TMPDIR`, `/tmp`, or `%TEMP%`. Use inline CSS and JavaScript so the report remains readable offline. External links to official sources are expected. Avoid framework and charting CDNs unless a diagram truly needs one.

The report should feel like a technical diagnostic, not a generic dashboard. Make the evidence easy to scan and the priorities hard to misread.

## Page structure

1. Header with repository, audited scope, date, commit, and a one-sentence diagnosis.
2. Detected stack table. Include role, evidence, installed version, current relevant stable version, and status.
3. Health strip for quality, cost, latency, overhead, visibility, reproducibility, and data handling. Use `Healthy`, `Needs attention`, `Unknown`, or `Not assessed`. Every status links to evidence below.
4. Top recommendation. State the change, why it wins, expected effect, confidence, effort, and first verification step.
5. Prioritized findings grouped as `Do now`, `Plan`, `Investigate`, and `Watch`.
6. Healthy choices to preserve.
7. Higher-level workflow opportunities. Include only ideas tied to observed recurring work or missing feedback.
8. Sources and audit limits, with access dates and unresolved uncertainty.

## Finding cards

Each card contains a direct title, confidence and effort badges, repository evidence, official guidance with a direct source link and access date, diagnosis, proposed change, expected effect, and the smallest verification. The verification names the signal that would accept or reject the change.

Use a compact before and after flow only when it explains a change better than prose. Prefer small inline SVG or styled HTML. Do not manufacture charts from qualitative judgments.

## Visual language

Use a neutral background, dark text, one cool accent, amber for uncertainty, and red only for active risk. Keep prose short. Tables should remain usable on a narrow screen. Add print styles. Use semantic HTML and visible focus styles.

Make evidence and inference visually distinct. A reader should be able to tell which claims came from the repository, which came from official documentation, and which are the auditor's deduction.

Do not bury weak evidence under a polished score. The health strip is navigation, not a numeric maturity model. Avoid an overall percentage or letter grade.
