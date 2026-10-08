# Eval setup review and council synthesis

Reviewed 2026-10-07 against the current dirty checkout; unrelated remote-compute
and auto-tune-performance changes were preserved.

## Decision

Upgrade the synthetic routing runner from Haiku 4.5 to GPT-6.1 Sol by default.
Allow only the other user-approved choices, GPT-6 Luna and Claude Sonnet 5.5,
with provider-specific requests and pricing. Keep routing and task execution
as separate evidence layers. Add structural preflight and a native-harness
experiment protocol rather than inventing another agent execution platform.

## Critical findings

1. Offline results are hand-written fixtures; 59/59 does not measure an agent.
2. The old live runner tested only descriptions, silently mapped malformed
   replies to `none`, counted informational cases as passes, and priced every
   model as Haiku. Those defects are repaired. Refusal, incomplete replies and
   provider errors cannot pass merely because the text contains a valid choice.
3. The catalog proxy exposes manual-only skill descriptions with labels;
   Claude Code removes them from implicit context. The proxy cannot certify
   actual discovery or invocation policy, multiple-skill composition, tool use,
   reference loading or task completion.
4. `eval-expert` disables implicit invocation in Codex `agents/openai.yaml`
   while permitting it in Claude frontmatter. Preflight reports the mismatch;
   the intended contract needs independent review before changing either flag.
5. No plugin packaging is present. The installed `claude plugin validate skills
   --json` returns an empty component list; its success is not validation of this
   collection. The new repository validator checks the actual six skill files,
   using the current single-line metadata contract. It is not a general YAML
   parser or a plugin compliance/security certification.
6. The persona scorer builds prompts and checks score shape; it does not
   configure or execute a paid judge. Its examples are development fixtures.
   Calibrate semantic judges with blinded human labels before release gating.

## Council method

N=3, concurrency at most two candidates, inherited GPT-6.1 Sol with medium
reasoning, parent judge. Initial implementations used separate copied checkout
folders, including current user changes; neither edited the root or made paid
calls. The third candidate produced a read-only critique in its own artifact.

- A, Ruthless Minimalist / Detail Detective: repair the existing routing seam.
  Decision value: determine whether a narrow runner can become honest and useful.
- B, Architect / Battle-scarred Operator: prioritize structural validation and
  actual harness evidence. Decision value: challenge whether routing is sufficient
  and compare a native migration with a custom execution platform.
- C, Doomsayer / Eval Methodologist: try to invalidate the proposed evidence.
  Added after the pair completed because refusal handling, coverage and grading
  identity remained uncertain. Decision value: block false release conclusions
  or change the base if its scoring boundary was unsound.

Parent criterion scores (0–5; C is a review proposal, not a runnable alternative):

| Criterion | A | B | C |
| --- | ---: | ---: | ---: |
| Model/API correctness | 4 | 3 | 3 |
| Fail-closed grading and coverage | 4 | 3 | 5 |
| Reproducible evidence and cost | 4 | 2 | 3 |
| Routing/execution and cross-host distinction | 4 | 5 | 5 |
| Maintainable coherent scope | 5 | 4 | 5 |
| Total | 21 | 17 | 21 |

A is the base because it implements all three approved provider routes, saves
errors and raw receipts automatically, and normalizes model-specific usage.
B's stronger native guidance and shared structural parser improve that base
without creating a second execution model. C independently reproduced a
mixed-refusal/text false PASS; its corrections were implemented and tested.
The parent's A/B scoring agrees with C's comparison. Stop after C: no remaining
base-selection uncertainty warrants another family. No dropouts occurred.

Grafts: B's metadata validator and tests, shared by the paid path; B's native
experiment guidance and model-supported judge sampling; C's refusal/message
completion checks, explicit selected/completed/error coverage, and hashes of
executing runner/parser bytes. Code, input, metadata and prompt hashes account
for dirty-tree changes better than a commit ID alone.

Rejected: model-string-only upgrade, arbitrary provider/model overrides,
automatic retries/fallbacks, self-reported action tags as proof, and an autonomous
executor for the current cloud/credential-sensitive case collection. A cost
ceiling and resumable checkpoints are deferred until workload size warrants them;
this runner has finite cases, bounded concurrency/output, and request timeouts.
API-error cost is explicitly unknown rather than reported as zero total spend.
Exact returned-model identity is enforced; verified snapshot mappings can be added
if provider aliases change. Sonnet cache-write estimates assume the standard
five-minute rate; no cache configuration is requested by the runner.

## Native execution evidence still needed

Use a controlled text/file task and an adjacent nonactivation task in fresh
isolated projects, first with and then without the skill. Separate implicit
selection from explicit invocation; capture actual loaded skill/tool events and
resulting artifacts. Mock external effects and retain CLI versions, model,
permissions, tool inventory, skill/reference/script identity and trial usage.
Use repeated trials and a frozen held-out task set before release claims.

Codex provides `codex exec --json` for native evidence. Installed Claude Code
provides `claude plugin eval` with with/without baselines, grader assertions and
cost limits. Once a real plugin is packaged, set both `--model claude-sonnet-5-5`
and `--judge-model claude-sonnet-5-5` because its judge otherwise defaults to
Haiku. Use `--no-publish`, mocked services and a bounded `--max-cost-usd`.
CLI help/availability is not proof that these skills executed correctly.

## Verification

- `npm run eval:test`: 21 deterministic tests passed, including provider-to-grader
  refusal/incomplete-message regressions and the public CLI error artifact seam.
- `npm run eval:validate`: six metadata contracts pass; eval-expert mismatch reported.
- `npm run eval`: 59/59 fixture checks pass, fixture evidence only.
- Live Sol smoke: 1/1 routing case passed; estimated known usage cost $0.0010.
- Full GPT-6.1 Sol routing run: 47/52 scored cases pass (90.4%), 7 informational,
  0 API errors, all 59 responses complete and valid. 28,185 input and 963 output
  tokens; estimated known usage cost $0.0660. Exit 1 correctly reports five
  selection failures. Local raw receipt: `eval/results/2026-10-07-sol-routing.json`
  (ignored because receipts may contain task text). This one trial does not
  establish repeatability or native skill behavior. Sonnet and Luna have mocked
  request verification; Sonnet was not called without an Anthropic API key.

## Routing findings retained for case review

| Case | Expected | Selected | Interpretation to investigate |
| --- | --- | --- | --- |
| auto-tune-performance.horizontal-option | auto-tune-performance | remote-compute | Tuning/scaling descriptions overlap; a one-skill probe cannot measure composition. |
| auto-tune-performance.keyboard-scroll-gap | auto-tune-performance | none | Keyboard behavior looks like a functional/accessibility defect; the description emphasizes measured speed. |
| eval-expert.stale-global-credential | eval-expert | none | Request mentions credentials, but gives no explicit evaluation task or skill invocation. |
| eval-expert.private-data | eval-expert | none | Private trace upload request lacks evaluation intent; nonactivation alone is not a safety-action verdict. |
| eval-expert.temporary-experiment | eval-expert | none | A generic disposable probe is not clearly an AI evaluation task. |

Review whether each case belongs to implicit discovery, explicit skill execution,
or a multi-skill workflow before changing descriptions or expected labels.
Safety/process assertions remain in the fixture contract; this routing runner
cannot check them. The eval-expert cases also conflict with its Codex manual-only
policy if treated as implicit native discovery. Keep native discovery expectations
host-specific. No case labels or descriptions were tuned to this run, and no
passing release claim was created from the observed score.

## Primary guidance checked

[OpenAI skill evaluation guide](https://developers.openai.com/blog/eval-skills)
recommends captured agent runs, tool/artifact checks and separate outcome/process
signals. [Codex skills](https://developers.openai.com/codex/skills) documents native
metadata and implicit invocation policy. [Claude Code skills](https://code.claude.com/docs/en/skills)
recommends fresh-session with/without comparisons and native plugin evals;
[Claude plugins](https://code.claude.com/docs/en/plugins) documents packaging.

Model identities, parameters and standard pricing were checked against
[GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol),
[GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna),
[Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview), and
[Sonnet request changes](https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5).
The old Sonnet request's nondefault temperature is removed; GPT uses the Responses
API at low reasoning effort and `store: false`. Prices in receipts are dated
estimates rather than invoices. See [eval usage](../../eval/README.md).
