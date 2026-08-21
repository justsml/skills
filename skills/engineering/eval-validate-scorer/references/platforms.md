# Platform notes for scorer validation

- **Braintrust:** Follow the scorer-validation workflow for reference-label tiers, agreement, confusion analysis, subgroup slices, shortcut probes, and explicit allowed or prohibited uses. Do not inherit generic cutoffs without fitting them to decision cost. [Source](https://github.com/braintrustdata/eval-library/blob/main/skills/braintrust-validate-eval-scorer/SKILL.md)
- **Promptfoo:** Encode bias probes and known calibration examples as executable tests, but calculate validity against independently reviewed labels outside the judge being tested. [Source](https://github.com/promptfoo/promptfoo/blob/main/plugins/promptfoo/skills/promptfoo-evals/SKILL.md)
- **Phoenix and LangSmith:** Use their experiment views to inspect scorer disagreements and trace context. Hosted evaluator output is evidence, not ground truth by itself.

Record the platform, judge model, prompt, scorer code, and dataset version with every validation result.
