---
name: eval-doctor
description: Audit an AI evaluation stack against current official platform and model-provider guidance. Use when the user wants a health check, modernization review, cost or latency review, observability assessment, dependency upgrade review, or a prioritized diagnosis of the repository's eval tooling and operating workflow.
---

# Eval doctor

Diagnose the evaluation system itself. Inspect what the repository runs today, verify relevant current guidance from official sources, and show the user the few changes most worth considering. This is an audit. Make changes only when the user asks.

## Establish the patient

Start with repository evidence. Read local agent instructions, manifests, lockfiles, eval and tracing configuration, CI workflows, representative eval code, result artifacts, and recent history for the affected paths. Search for model identifiers, provider SDKs, dataset handling, scorers, experiment runners, tracing, retries, concurrency, caching, sampling, usage accounting, and release gates.

Detect the active stack rather than assuming one from an installed package. Corroborate dependencies and config with call sites, scripts, environment variable names, CLI configuration, CI, or recent run artifacts. Distinguish model providers and gateways, eval or observability platforms, local runners and scorers, production feedback paths, and CI enforcement.

Treat secrets as presence signals only. Never print their values. A platform that appears only in a stale lockfile or unused environment key is not active without stronger evidence.

State the audit scope and detected stack before drawing conclusions. If two active configurations remain plausible, audit their shared implementation and label the ambiguity. Ask only when choosing one would materially change the findings.

## Build a current baseline

Freshness is part of the job. Browse the official documentation, release notes, migration guides, pricing pages, model catalogs, and SDK references for each detected provider or platform. Prefer primary sources and installed-version documentation. For technical claims, use official sources only.

Record the access date, installed version or commit evidence, latest relevant stable version, and source URL. Check release dates and version compatibility before recommending an upgrade. Do not treat a newer version as better by default. Name the capability, fix, price change, or removed limitation that makes the upgrade useful here.

If official sources disagree, show the conflict and prefer the source closest to the installed version and feature. Mark preview, beta, deprecated, region-limited, and enterprise-only features clearly. Separate documented facts from deductions about the repository.

Do not run paid evals or send repository data to hosted scanners, providers, or observability platforms during the audit. Read-only account or CLI checks are fine when already authenticated and they do not upload project data.

## Examine the whole loop

Follow one representative case through dataset selection, candidate execution, scoring, aggregation, storage, comparison, and release decision. Then inspect the surrounding system for findings that would change quality, spend, speed, or confidence.

Pay particular attention to:

- whether metrics represent product claims and known failure modes
- dataset versioning, split isolation, leakage, slices, and production feedback
- scorer validity, calibration, nondeterminism, judge bias, and provenance
- model and SDK lifecycle, structured outputs, batch or cached execution, routing, and token controls
- concurrency, retry classification, backoff, rate limits, duplicate calls, and failure recovery
- trace coverage, experiment identity, prompt and model versions, token and cost capture, latency distributions, and error visibility
- reproducibility, CI gates, flaky thresholds, baseline age, artifact retention, and ownership
- privacy, redaction, retention, regional processing, and unintended data export
- workflow gaps where a small automation, shared abstraction, or feedback loop would remove recurring manual work

Measure before claiming an improvement. Use existing run data when possible. If evidence is missing, estimate a range from documented pricing and observed call shapes, show the assumptions, and label it an estimate. Never invent savings or performance gains.

Prefer findings with a plausible path to action. A feature that cannot address an observed constraint belongs in the watch list, not the recommendation list.

## Rank findings

Give each finding observed evidence, current official guidance, a diagnosis, the proposed change, the smallest useful verification, and the expected effect on quality, cost, latency, overhead, or visibility. Assign:

- confidence: `High`, `Medium`, or `Low`
- effort: `Small`, `Medium`, or `Large`
- recommendation: `Do now`, `Plan`, `Investigate`, or `Watch`

Reserve `Do now` for well-supported, low-regret changes. Put migrations, architectural changes, and uncertain optimizations behind a proof step. Include a finding only when its expected value exceeds its adoption and maintenance cost.

Also record what is healthy and should remain unchanged. This prevents a future audit from reopening settled choices without new evidence.

## Present the diagnosis

Read [references/report.md](references/report.md) and write a self-contained HTML report to the OS temporary directory. Open it for the user and give them the absolute path. Keep the repository unchanged.

Surface serious findings as soon as the evidence is clear, especially leaked held-out data, silent scorer failures, uncontrolled spend, unsupported versions, missing usage records, or privacy risks. Do not hold these for the report.

End with one top recommendation and a short sequence of the next two or three actions. Ask which finding the user wants to pursue. Do not implement the recommendations until asked.

## Completion

Finish when every detected active provider and platform has an official-source freshness check, the representative evaluation path has been traced end to end, each recommendation cites repository and external evidence, uncertainty is explicit, and the report separates immediate work from ideas that need proof.
