---
name: eval-build-dataset
description: Build or revise versioned evaluation datasets for AI systems. Use when traces, incidents, requirements, or synthetic cases must become development, validation, held-out, adversarial, or regression sets with defensible provenance.
---

# Build an eval dataset

Make the dataset a durable, portable asset. A framework can be replaced; reviewed cases and their provenance cannot.

## Define the case contract

Give every case a stable ID, input and context, expected evidence or acceptable behavior, failure-mode and slice tags, provenance, split, sensitivity, and label status. Represent multiple valid outcomes when the task permits them. For agents, record end-state invariants and only those trajectory constraints that the product actually requires.

## Curate the portfolio

Start with real tasks and observed failures. Add deliberate boundary, adversarial, and counterexample cases. Use synthetic generation to fill named coverage gaps, then review those cases before they can support a release decision.

Deduplicate semantically across splits. Keep optimization examples out of the held-out set, including paraphrases and trace descendants. Record exclusions and `not assessed` reasons so coverage is assessed over applicable cases rather than an imaginary universal set.

Minimize sensitive records while preserving the failure mechanism. Follow the data owner's retention and consent rules. Get explicit approval before uploading private traces or datasets to a hosted service.

If storage depends on a particular service or framework, read [the platform notes](references/platforms.md) only for the selected platform.

## Completion

Finish with a versioned manifest, split counts by important slice and failure mode, provenance and sensitivity coverage, deduplication results, unresolved label disagreements, and a changelog or diff from the prior version.
