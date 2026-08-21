# Langfuse evaluation platform analysis

Research date: 2026-08-21

Scope: Langfuse as a platform-specific implementation target for the provider-neutral `eval-*` skills in this repository. Sources are limited to current official Langfuse documentation, official Langfuse repositories, and first-party API or SDK references.

## Recommendation

Add Langfuse notes to each action-specific `references/platforms.md` file. Do not create one large Langfuse skill. A single platform skill would force agents to load trace ingestion, prompt deployment, dataset mutation, evaluator runtime, and CI details when most tasks need only one of them. Keep this research note as the detailed source and place short operational rules next to the neutral skill that uses them.

Langfuse is a good implementation target for five parts of the lifecycle:

- mining production observations and sessions;
- promoting reviewed trace evidence into versioned datasets;
- running and comparing offline experiments;
- storing scores from local, hosted-code, judge, and human evaluators;
- connecting prompt versions to traces and experiment results.

It should not own the neutral evaluation contract. Important semantics differ from the repository's abstractions. Langfuse calls an execution over a hosted dataset an experiment or dataset run, represents all evaluation outputs as scores, and treats a session as a grouping of traces rather than a trajectory object with a guaranteed assembled state. Observation-targeted hosted evaluators see one matched observation, not its sibling or child observations. [Evaluation concepts](https://langfuse.com/docs/evaluation/core-concepts), [observability data model](https://langfuse.com/docs/observability/data-model), [LLM-as-a-Judge](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)

## Concept mapping

| Neutral concept | Langfuse object | Important qualification |
| --- | --- | --- |
| case | dataset item | Has `input`, optional `expectedOutput`, metadata, optional source trace and observation IDs. |
| dataset revision | dataset version timestamp | Item add, update, delete, or archive creates a new timestamped version. Schema changes do not create a dataset version. |
| candidate execution | experiment item trace | Hosted-dataset experiments also create a dataset run. Local-data experiments create traces but no dataset run. |
| experiment | experiment run / dataset run | Item evaluators produce trace-level scores; run evaluators can attach aggregate scores to a hosted dataset run. |
| scorer output | score | Typed as numeric, boolean, categorical, text, or correction in Scores API v3. A score is evidence, not a validated metric. |
| request / trajectory step | trace / observation | A trace groups observations by `trace_id`. Observations are the stored rows and can be nested. |
| conversation / thread | session | A `sessionId` groups observations across traces. It is not itself an automatically reconstructed agent state. |
| prompt revision | immutable prompt version | Labels such as `production` and `latest` are mutable pointers. Fetch by version for reproducibility. |
| human review batch | annotation queue | Queue items target traces, observations, or sessions and require score configs. |

Sources: [datasets](https://langfuse.com/docs/evaluation/experiments/datasets), [experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk), [Scores API v3](https://langfuse.com/docs/api-and-data-platform/features/scores-api), [annotation queues](https://langfuse.com/docs/evaluation/evaluation-methods/annotation-queues), [prompt concepts](https://langfuse.com/docs/prompt-management/data-model).

## Datasets, items, versions, and runs

Langfuse datasets hold test items with `input`, optional `expected_output` / `expectedOutput`, metadata, and optional links back to a source trace and observation. JSON Schema can validate dataset input and expected-output fields. Dataset item mutations create timestamped dataset versions. Schema changes do not, so a reproducibility manifest must record both the dataset version timestamp and the schema separately. Reads default to the latest dataset version unless a `version` timestamp is supplied. Archive removes an item from future experiment runs without erasing its historical versions. [Dataset documentation and SDK examples](https://langfuse.com/docs/evaluation/experiments/datasets)

Use stable caller-owned item IDs when syncing a repo-owned dataset. Dataset item IDs are project-global and cannot be reused across datasets. `create_dataset_item` is an upsert when supplied an existing item ID, so an accidental ID collision mutates the existing case and advances the hosted dataset version. Adding, updating, deleting, and archiving items are external mutations. Record the returned item ID, source IDs, exact version timestamp, schema digest, and sync tool version. [Experiments data model](https://langfuse.com/docs/evaluation/experiments/data-model)

Python pattern:

```python
from datetime import datetime, timezone
from langfuse import get_client

langfuse = get_client()
langfuse.create_dataset(name="support/regression-v1")
langfuse.create_dataset_item(
    id="case-refund-001",
    dataset_name="support/regression-v1",
    input={"question": "Can I return this?"},
    expected_output={"policy": "eligible"},
    metadata={"slice": "refunds", "source_revision": "git-sha"},
    source_trace_id="trace-id",
    source_observation_id="observation-id",
)

dataset_version = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
dataset = langfuse.get_dataset("support/regression-v1", version=dataset_version)
```

JS/TS pattern:

```ts
import { LangfuseClient } from "@langfuse/client";

const langfuse = new LangfuseClient();
const datasetName = "support/regression-v1";
await langfuse.dataset.create(datasetName);
const dataset = await langfuse.dataset.get(encodeURIComponent(datasetName), {
  version: new Date("2026-08-21T12:00:00Z").toISOString(),
});
```

Names containing `/` require URL encoding in JS/TS path-based fetches. Multi-modal hosted datasets work in SDK experiments with Python SDK 4.10.0 or newer and `@langfuse/client` 5.6.0 or newer, but UI experiments do not support media dataset items at the time of research. [Dataset folders and media support](https://langfuse.com/docs/evaluation/experiments/datasets)

There is current documentation drift worth calling out. The dataset page documents running experiments against a fetched versioned dataset, while the general SDK and UI experiment pages still say experiments always use the latest version and that version pinning is forthcoming. Prefer the newer versioned-dataset pattern, verify it against the installed SDK, and store the actual dataset version timestamp reported by the run. Do not infer reproducibility from a run name. [Versioned datasets](https://langfuse.com/docs/evaluation/experiments/datasets), [experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk), [experiments via UI](https://langfuse.com/docs/evaluation/experiments/experiments-via-ui)

## Experiments and regression execution

SDK experiments accept local arrays or hosted Langfuse datasets. Local data creates one trace per task execution but no dataset run. Hosted datasets create a dataset run that Langfuse can compare in the UI. Item evaluators run in the client process and receive input, output, expected output, and metadata. Run evaluators receive all item results and can attach aggregate scores to a hosted dataset run. JS/TS experiment tracing requires an OpenTelemetry setup and an explicit shutdown or flush at process end. [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)

Python pattern:

```python
from langfuse import Evaluation, get_client

langfuse = get_client()
dataset = langfuse.get_dataset("support/regression-v1", version=dataset_version)

def task(*, item, **kwargs):
    return app_under_test(item.input)

def exact_policy(*, output, expected_output, **kwargs):
    passed = output["policy"] == expected_output["policy"]
    return Evaluation(name="policy_exact", value=passed, comment="deterministic equality")

result = dataset.run_experiment(
    name="candidate-git-sha",
    description="Pinned candidate and dataset version",
    task=task,
    evaluators=[exact_policy],
)
print(result.format())
```

JS/TS pattern:

```ts
const result = await dataset.runExperiment({
  name: "candidate-git-sha",
  task: async (item) => appUnderTest(item.input),
  evaluators: [async ({ output, expectedOutput }) => ({
    name: "policy_exact",
    value: output.policy === expectedOutput.policy,
    comment: "deterministic equality",
  })],
});
await otelSdk.shutdown();
```

The first-party `langfuse/experiment-action` GitHub Action can run Python or JS experiment scripts, inject dataset name, dataset version, and metadata, comment on a pull request, and fail when a script raises its regression error. Pin the action and SDK version in CI rather than relying on its defaults. The action needs Langfuse project keys and may need `pull-requests: write`; using it sends test inputs, outputs, traces, and scores to the configured Langfuse instance. [Official experiment action](https://github.com/langfuse/experiment-action)

The Experiments API retrieves runs, summaries, experiment items, item inputs and outputs, expected outputs, metadata, scores, and trace IDs. Use Observations API v2 to retrieve the full observation tree and Scores API v3 for score-centric reads. The API does not replace the runner for executing tasks. Langfuse currently represents at most one experiment item per dataset item within a run, so repeated trials need separate runs or distinct dataset items and external aggregation. [Experiments API](https://langfuse.com/docs/api-and-data-platform/features/experiments-api), [experiments data model](https://langfuse.com/docs/evaluation/experiments/data-model)

## Scores and evaluator implementations

Scores are the common storage object for human labels, user feedback, deterministic checks, external pipelines, and LLM judges. They can attach to traces, observations, sessions, or dataset runs. Score configs define allowed dimensions for UI and annotation workflows. Scores API v3 returns one typed `value`; consumers must branch on `dataType`. Text scores are not aggregatable and are not supported by experiments, LLM judges, or score analytics. Score configs are immutable, though they can be archived and restored. [Score overview](https://langfuse.com/docs/evaluation/scores/overview), [score data model](https://langfuse.com/docs/evaluation/scores/data-model), [Scores API v3](https://langfuse.com/docs/api-and-data-platform/features/scores-api)

When ingesting scores, provide a stable ID as an idempotency key. Langfuse only overwrites an existing score when ID, name, and timestamp at date granularity all match. A stable ID alone does not prevent duplicates if the name or date changes. This is unusually easy to get wrong in re-evaluation jobs. Preserve score ID, name, timestamp, scorer code digest, judge prompt version, judge model and settings, dataset version, and target trace or observation ID. [Score update and duplicate semantics](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk)

Langfuse offers three evaluator execution locations:

- SDK evaluator functions run in the experiment process. These are the best fit for repo-owned, testable scorer code.
- Hosted code evaluators run Python or TypeScript against observations or experiments. They have no third-party packages or network access, a two-second runtime limit, a 5.5 MB input limit, and a 256 KB source and result limit. The public evaluator endpoints are marked unstable. Use an external pipeline and ingest scores when those constraints do not fit. [Code evaluators](https://langfuse.com/docs/evaluation/evaluation-methods/code-evaluators)
- Hosted LLM-as-a-Judge evaluators run asynchronously against matched live observations or experiments. Evaluators define prompt, variables, output definition, and optional model. Rules define target, filters, sampling, and field mappings. Evaluators are versioned; creating one with an existing name creates the next version, and active rules move to it. That automatic move is convenient for monitoring but weakens reproducibility unless the evaluator version and resolved model configuration are recorded. [LLM-as-a-Judge](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)

Observation-level hosted evaluators only receive the matched observation fields. They do not load sibling or child observations. For end-to-end agent judging, write the necessary assembled input, output, and trajectory summary onto a logical root observation, or evaluate outside Langfuse after reconstructing the trace from Observations API v2. A single rule can match multiple observations and create multiple scores per trace. This differs from a neutral "one score per case" contract. [LLM-as-a-Judge target semantics](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)

For self-hosted code evaluators, `insecure-local` executes trusted TypeScript or JavaScript inside the Langfuse worker and is explicitly not a sandbox boundary. The AWS Lambda dispatcher supports Python, but the operator must isolate evaluator execution and network access. Treat enabling or changing the dispatcher as an infrastructure security change. [Self-hosted code evaluators](https://langfuse.com/self-hosting/configuration/code-evaluators)

## Human review and annotation queues

Annotation queues assign traces, observations, or sessions to domain experts. A queue requires score configs, can assign users, supports score comments and corrected outputs, and tracks each queue item as a task. Use queues for blinded calibration sets, disagreement review, and production-failure labeling. Do not treat an annotation score as ground truth until the review protocol defines annotator identity, rubric version, adjudication, and allowed use. [Annotation queues](https://langfuse.com/docs/evaluation/evaluation-methods/annotation-queues)

The Public API can list queues and items, add items, patch queue items, and remove them. `POST` and `PATCH` mutate shared review state. `DELETE /api/public/annotation-queues/{queueId}/items/{itemId}` removes an item from a queue and should require an explicit target list and confirmation for broad operations. [Annotation Queue API announcement and endpoints](https://langfuse.com/changelog/2025-03-13-public-api-annotation-queues)

Use separate score configs or explicit metadata for human reference labels and model-produced scores. A matching score name alone does not establish provenance. Export label evidence before changing configs or queue membership.

## Traces, observations, and sessions

Langfuse uses OpenTelemetry. Observations represent spans, generations, and events and may nest. A trace is the logical group sharing `trace_id`. Trace-level fields such as user, session, tags, metadata, release, and version are copied onto observations when instrumentation propagates them. Sessions group observations across traces by `sessionId`; the ID must be a US-ASCII string shorter than 200 characters. [Observability data model](https://langfuse.com/docs/observability/data-model), [sessions](https://langfuse.com/docs/observability/features/sessions)

For trace mining:

- Query Observations API v2 with bounded `fromStartTime` and `toStartTime` ranges and cursor pagination.
- The v2 endpoint returns observation rows, not assembled trace objects. Group by `traceId` and restore parent relationships when trajectory shape matters.
- There is no v2 get-by-ID route. Use its encoded filter on `id`.
- Prefer Metrics API v2 for aggregates instead of downloading raw observations.
- Data from Python SDK older than 4.7.0, JS/TS SDK older than 5.4.0, or direct OTEL exporters without `x-langfuse-ingestion-version: 4` can appear up to 15 minutes late in v2 reads. This can make a just-ingested online-eval sample look incomplete. [Observations API v2](https://langfuse.com/docs/api-and-data-platform/features/observations-api)

Trace sampling and redaction happen before evidence reaches the mining workflow, so document both as selection bias. For evaluation rules based on trace-level attributes, Langfuse requires those attributes to be propagated to observations. A missing propagated field is not proof the source trace lacked that context.

## Prompt management and reproducibility

Langfuse prompt versions are immutable integers. Labels such as `production`, `latest`, and custom stage labels point to versions and can move. Prompt type cannot change after creation. Prompt configuration is versioned with the prompt and can hold model settings, schemas, tools, and tool choice. Link the resolved prompt object to the generation observation so Langfuse can attribute metrics and scores to the exact prompt version. [Prompt concepts](https://langfuse.com/docs/prompt-management/data-model), [prompt config](https://langfuse.com/docs/prompt-management/features/config), [link prompts to traces](https://langfuse.com/docs/prompt-management/features/link-to-traces)

SDK prompt caching can temporarily serve an older version after a label moves. Fetch a numeric version during evaluation and record the prompt name, numeric version, compiled content digest, config, model parameters, and any referenced prompt versions. If a label must be tested, resolve and record its numeric version. Set cache TTL to zero only when freshness is required and the availability tradeoff is accepted. [Prompt caching and labels](https://langfuse.com/docs/prompt-management/data-model), [prompt get/create examples](https://langfuse.com/docs/prompt-management/get-started)

Composed prompts can reference another prompt by numeric version or mutable label. A parent prompt version that contains a label reference does not by itself freeze the resolved child content. Pin child versions or record the complete resolved dependency graph for reproducible experiments. [Prompt composability](https://langfuse.com/docs/prompt-management/features/composability)

Creating a prompt with an existing name creates a new version. Assigning `production` changes live application behavior after cache propagation. Treat prompt creation, label movement, and config changes as external mutations. Require explicit approval for production-label movement.

## Online and offline evaluation

Langfuse's offline loop uses datasets and experiments before deployment. Its online loop applies judge, code, human, or externally ingested scores to live observations, traces, or sessions. Production failures can be linked back into datasets with `source_trace_id` and `source_observation_id`. [Evaluation concepts](https://langfuse.com/docs/evaluation/core-concepts), [create dataset items from production data](https://langfuse.com/docs/evaluation/experiments/datasets)

Keep the two populations separate in analysis. Online rules can filter and sample live observations, so their score distribution reflects both production traffic and the rule's selection function. Offline experiments use the chosen dataset version and execution configuration. Never compare their aggregate scores without preserving target type, filters, sample rate, time bounds, environment, release, and scorer version.

Langfuse evaluation jobs are asynchronous. Flush the SDK or OTEL processor before process exit, and allow for ingestion and evaluator lag before declaring cases missing. Separate task errors, trace-delivery errors, evaluator errors, and failed metric gates.

## OpenTelemetry, API, CLI, and export

OpenTelemetry is the supported trace-ingestion path. Langfuse's legacy trace and observation Ingestion API is deprecated and scheduled to sunset on Langfuse Cloud on 2026-11-16. Current SDK score helpers remain supported after that cutover. For direct OTEL ingestion, set the current ingestion-version header when required by the v2 read path and verify span attribute mappings against the current integration guide. [Public API and ingestion status](https://langfuse.com/docs/api-and-data-platform/features/public-api)

The project Public API uses HTTP Basic authentication with a project public key and secret key. Base URLs are region-specific. Python SDK v4 and JS/TS SDK v5 expose typed API clients, with `observations`, `metrics`, and Scores API v3 as the current high-performance resources. Deprecated resources live under legacy namespaces. [Public API](https://langfuse.com/docs/api-and-data-platform/features/public-api)

The official CLI dynamically wraps the OpenAPI specification:

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_BASE_URL="https://cloud.langfuse.com"
npx langfuse-cli api observations list --limit 100 --all --max-items 5000
```

There is no separate CLI login. Keys are project-scoped. The CLI can call mutating and destructive endpoints because it wraps the whole API, so discover the endpoint and inspect targets before executing writes. Its documented exit codes distinguish usage, configuration, network, HTTP, and local errors. Prefer a pinned CLI version in automation. [Langfuse CLI](https://langfuse.com/docs/api-and-data-platform/features/cli), [official CLI repository](https://github.com/langfuse/langfuse-cli)

For extraction, use Observations API v2 for row-level telemetry, Scores API v3 for raw scores, Experiments API for run and item records, Metrics API v2 for aggregates, UI export for bounded one-off work, and blob-storage export for scheduled high-volume copies. Blob export contains enriched observations and scores, not prompts, datasets, evaluator configurations, or a complete portable project backup. [API and data platform](https://langfuse.com/docs/api-and-data-platform/overview), [blob-storage export](https://langfuse.com/docs/api-and-data-platform/features/export-to-blob-storage)

## Cloud, self-hosting, privacy, and upload boundaries

Langfuse Cloud has separate EU, US, Japan, and HIPAA US regions with separate accounts and infrastructure. Switching regions requires an account and data migration. Project keys and API base URL must point to the same region. Langfuse says Cloud customer traces and prompts are not used to train internal or third-party models. Cloud stores submitted data as-is unless the client masks it. [Data regions](https://langfuse.com/security/data-regions), [security FAQ](https://langfuse.com/security/security-faq)

Any trace ingestion, dataset sync, experiment, score upload, annotation write, prompt write, or hosted evaluator can transmit application input, output, metadata, retrieved context, media, user or session identifiers, and judge reasoning. Get explicit approval before broad or private uploads. Use client-side masking when sensitive data must not leave the application. Collector-side masking occurs after data leaves the application trust boundary. [Masking](https://langfuse.com/docs/observability/features/masking)

Langfuse supports self-hosting, but that transfers operational responsibility. Current architecture uses web and worker containers, Postgres, ClickHouse, Redis or Valkey, and S3-compatible blob storage. Backing services should not be exposed publicly. Self-hosting does not make evaluator calls private if a configured judge model sends data elsewhere. [Architecture](https://langfuse.com/handbook/product-engineering/architecture), [self-host hardening](https://langfuse.com/self-hosting/configuration/hardening)

Cloud trace deletion also removes related observations and scores. Trace deletion is asynchronous and usually completes within 15 minutes; there is no deletion notification, so verify with a read. Retention can delete a source trace while its dataset-run reference survives, leaving incomplete lineage. Project deletion immediately revokes API keys and irreversibly schedules all project data for deletion. Queue-item removal, dataset item archive or deletion, prompt-label movement, evaluator or rule creation, and score overwrite also mutate shared state even when they are less destructive. [Data deletion](https://langfuse.com/docs/administration/data-deletion), [data retention](https://langfuse.com/docs/administration/data-retention)

## Limitations and semantic gaps to preserve in skill instructions

1. A Langfuse score is a storage record, not proof of scorer validity. Calibration stays in `eval-validate-scorer`.
2. Observation-targeted evaluators do not automatically see a trace trajectory. Reconstruct it or log an explicit root summary.
3. A session groups traces but does not define turn ordering, state transitions, or a task-success contract by itself.
4. Dataset versioning is timestamp-based and excludes schema changes. Store schema and content provenance separately.
5. Local-data experiments create traces but no dataset run. Do not promise hosted run comparisons in that mode.
6. Labels are mutable. Prompt label names and evaluator family names are not reproducible identifiers.
7. Prompt caching can make the resolved production prompt lag behind a label change.
8. Hosted code evaluators have strict runtime and dependency limits. Self-hosted `insecure-local` is not a sandbox.
9. Online and offline score aggregates describe different populations and selection processes.
10. Current official pages disagree on whether all experiment paths can pin dataset versions. Verify the installed SDK and record the run's actual dataset version.
11. Observations API v2 returns rows, not full trace objects, and older ingestion paths can delay visibility.
12. API and CLI access includes destructive operations. Project-scoped credentials do not imply read-only access.

## Suggested exact edits by skill

These are deliberately short enough for the sibling platform files. They should be inserted as a `Langfuse` bullet, with the cited links retained.

### `eval-design/references/platforms.md`

> - **Langfuse:** Map cases to dataset items, executions to experiment item traces, evaluator outputs to typed scores, and conversations to sessions only when the application supplies a stable `sessionId`. Keep the neutral decision rule outside Langfuse: a score is a storage object, online observation rules can sample a filtered population, and observation evaluators do not load sibling or child observations. [Concepts](https://langfuse.com/docs/evaluation/core-concepts) [Judge targets](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)

### `eval-mine-traces/references/platforms.md`

> - **Langfuse:** Query Observations API v2 with bounded time filters and cursor pagination. It returns observation rows, not assembled traces; group by `traceId`, restore parent links, and use `sessionId` only as a cross-trace grouping key. Record environment, release, version, sampling, masking, and ingestion lag. Observation-targeted evaluators cannot see sibling or child spans unless the application copies the required context to the logical root. [Observations API v2](https://langfuse.com/docs/api-and-data-platform/features/observations-api) [Data model](https://langfuse.com/docs/observability/data-model)

### `eval-build-dataset/references/platforms.md`

> - **Langfuse:** Preserve caller-owned item IDs plus `source_trace_id` and `source_observation_id` when promoting reviewed failures. Pin the dataset version timestamp for runs and store the JSON Schema separately because item mutations create versions but schema changes do not. Archive excludes an item from future runs; upserting an existing ID mutates shared data. Verify version pinning against the installed SDK because current experiment pages disagree. [Datasets](https://langfuse.com/docs/evaluation/experiments/datasets) [SDK experiments](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)

### `eval-build-scorer/references/platforms.md`

> - **Langfuse:** Prefer repo-owned SDK evaluators for testable scorer code, or ingest external results as scores. Hosted code evaluators have no network or third-party packages, a two-second limit, and unstable management endpoints. Hosted observation evaluators see only the matched observation. Use stable score IDs and preserve name and timestamp too, since all three must match for overwrite semantics. [Code evaluators](https://langfuse.com/docs/evaluation/evaluation-methods/code-evaluators) [Scores via SDK](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk)

### `eval-validate-scorer/references/platforms.md`

> - **Langfuse:** Use annotation queues and score configs to collect human labels on traces, observations, or sessions, then export reviewer identity, rubric/config version, comments, corrections, and adjudication state for calibration. Keep human and judge provenance distinct even when score names match. Evaluator families are versioned and active rules move to new versions, so pin the evaluated version and resolved judge model before validity analysis. [Annotation queues](https://langfuse.com/docs/evaluation/evaluation-methods/annotation-queues) [LLM-as-a-Judge](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)

### `eval-run-regressions/references/platforms.md`

> - **Langfuse:** Hosted-dataset SDK experiments create comparable dataset runs; local-data experiments create traces only. Record dataset version timestamp and schema digest, prompt numeric version and resolved references, candidate revision, model settings, scorer versions, run ID/name, and raw item evidence. JS/TS runs require OpenTelemetry setup and shutdown/flush. Separate task, ingestion, evaluator, and gate failures. [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk) [Prompt versions](https://langfuse.com/docs/prompt-management/data-model)

### `eval-optimize/references/platforms.md`

> - **Langfuse:** Use experiment history and trace-linked prompt versions as evidence, but run search outside Langfuse unless its bounded UI experiment flow is sufficient. Fetch prompts by numeric version, not mutable label, and record compiled content, config, referenced prompt versions, and cache behavior for every candidate. Creating prompt versions or moving `production` is an external mutation; keep held-out data outside optimizer feedback. [Prompt concepts](https://langfuse.com/docs/prompt-management/data-model) [Prompt composability](https://langfuse.com/docs/prompt-management/features/composability)

### `eval-planner/SKILL.md`

No platform-specific paragraph is needed in the thin coordinator. If the planner has a platform-routing sentence, add Langfuse alongside Braintrust, LangSmith, Phoenix, and Promptfoo as an implementation target and route details to the sibling platform files. Do not put API commands or object-model explanations in the planner.

## Source set

- [Langfuse evaluation overview](https://langfuse.com/docs/evaluation/overview)
- [Evaluation core concepts](https://langfuse.com/docs/evaluation/core-concepts)
- [Datasets](https://langfuse.com/docs/evaluation/experiments/datasets)
- [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
- [Experiments API](https://langfuse.com/docs/api-and-data-platform/features/experiments-api)
- [Scores overview](https://langfuse.com/docs/evaluation/scores/overview)
- [Scores via API and SDK](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk)
- [Scores API v3](https://langfuse.com/docs/api-and-data-platform/features/scores-api)
- [LLM-as-a-Judge](https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge)
- [Code evaluators](https://langfuse.com/docs/evaluation/evaluation-methods/code-evaluators)
- [Annotation queues](https://langfuse.com/docs/evaluation/evaluation-methods/annotation-queues)
- [Observability data model](https://langfuse.com/docs/observability/data-model)
- [Observations API v2](https://langfuse.com/docs/api-and-data-platform/features/observations-api)
- [Sessions](https://langfuse.com/docs/observability/features/sessions)
- [Prompt management concepts](https://langfuse.com/docs/prompt-management/data-model)
- [Prompt management get started](https://langfuse.com/docs/prompt-management/get-started)
- [Prompt config](https://langfuse.com/docs/prompt-management/features/config)
- [Prompt composability](https://langfuse.com/docs/prompt-management/features/composability)
- [Link prompts to traces](https://langfuse.com/docs/prompt-management/features/link-to-traces)
- [Public API](https://langfuse.com/docs/api-and-data-platform/features/public-api)
- [Langfuse CLI](https://langfuse.com/docs/api-and-data-platform/features/cli)
- [API and data platform](https://langfuse.com/docs/api-and-data-platform/overview)
- [Data masking](https://langfuse.com/docs/observability/features/masking)
- [Data deletion](https://langfuse.com/docs/administration/data-deletion)
- [Data regions](https://langfuse.com/security/data-regions)
- [Security FAQ](https://langfuse.com/security/security-faq)
- [Platform architecture](https://langfuse.com/handbook/product-engineering/architecture)
- [Self-host hardening](https://langfuse.com/self-hosting/configuration/hardening)
- [Self-hosted code evaluators](https://langfuse.com/self-hosting/configuration/code-evaluators)
- [Official Python SDK](https://github.com/langfuse/langfuse-python)
- [Official JS/TS SDK](https://github.com/langfuse/langfuse-js)
- [Official experiment action](https://github.com/langfuse/experiment-action)
- [Official CLI](https://github.com/langfuse/langfuse-cli)
