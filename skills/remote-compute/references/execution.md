# Remote execution and recovery

## Before provisioning

Record a stable run ID, effective project policy and authorization source, source revision/dirty patch hashes, input manifest, workload command, job partitions, output path, completion signal, budget, deadline and cleanup reserve. Inventory pre-existing resources. The ownership manifest binds project/run/account/region, exact resource IDs and types, creation/billable timestamps, rates and provenance, attachments, lifecycle action, cleanup supervision and receipts. Register the creation label before creation; capture the stable ID immediately afterward.

Reconcile an uncertain create response against pre-existing inventory, run labels, timestamp and provider idempotency before retrying. Provision a small pilot first. No unbounded create/retry loop. A replacement consumes the same run budget and retains previous accrued costs.

Use only authorized source/data/secrets. Prefer restricted per-run capabilities with expiry and revocation. Keep provisioning/account keys and SSH private keys on the coordinator. A user may already have authorized local SSH authentication; that never permits copying the private identity or forwarding an agent. Record approved workload-secret destinations and removal/revocation. Deletion of a host does not revoke copied secrets.

## Bootstrap and prove the actual workload

Use a task-owned clone/worktree, directory, service name, ports and output location. Create Git worktrees on the destination rather than copying their coordinator `.git` pointers. Stage the exact source and explicitly approved dirty/untracked files; exclude secret paths and unrelated data. Record base commit plus patch/input hashes. Pin compatible OS/architecture/runtime, image and lockfile dependencies using the project's package manager. Do not assume an interactive shell's PATH exists under SSH/systemd/launchd.

Check actual free disk/inodes, RAM/VRAM, GPU/driver/runtime compatibility, network and required services from the real job container. `/tmp` may be a small RAM filesystem. Container Pods/sandboxes may lack a daemon or privileged features. Start one representative build, import chunk, inference request or eval case; verify actual output and exit state, not just a health endpoint. Include bootstrap/pilot overhead in the budget and reuse valid outputs where appropriate.

Large imports need stable item IDs, checkpoints and idempotent writes so disconnects/retries do not duplicate data. Freeze eval datasets, routes and scoring, preserve every attempt and distinguish infrastructure failures from candidate quality; apply the project's own eval/target authorization contracts. This general skill grants no permission for security probes or exploitation.

## Schedule and supervise

Use a durable queue with atomic claims or immutable non-overlapping partitions. Give jobs a stable ID, isolated mutable state, bounded timeout/retry count, log, process/service identity, completion/failure state and output receipt. Multiple threads coordinate provider ownership and aggregate budgets. A borrowed host has a reserved capacity allocation and preserve-host cleanup policy.

Parallelism is limited by the actual bottleneck: memory, VRAM/KV cache, I/O, bandwidth, downstream API quotas or shared services, as well as CPU. Start conservatively and raise useful concurrency from measured headroom. High hardware usage with no useful progress is not success. Treat provider-waiting requests as active work. On contention/OOM/timeout, reduce concurrency and verify a narrow recovery before reopening affected queues.

On SSH loss, inspect the same durable job before resubmission; disconnected does not mean stopped. Pause admissions for affected infrastructure. Keep healthy independent lanes running when budget and isolation allow; shared storage/database/provider/supervisor faults stop all affected lanes. Preserve failures and partial outputs; retry only bounded transient faults or after a verified prerequisite change. Stop near-total failure rather than burning the full matrix.

Checkpoint artifacts off-host and publish costs/ETA under [monitoring](monitoring.md). A capacity extension must fit existing aggregate permission or obtain a concrete extension. Renewing/restarting cleanup must preserve spend, ownership and liveness history.

## Finish or stop

Stop new admissions and reconcile active jobs. Copy artifacts, logs, hashes and source/config fixes back to the coordinator. Integrate worker fixes as reviewable changes and run relevant checks; identify remote-only validation accurately. Do not erase uncollected worker edits during refresh.

For owned paid resources, perform bounded final sync, shut down credential holders and revoke/remove approved secret copies, then retire exact resources and attachments through the provider's official lifecycle. Verify no autoscaler/schedule can recreate them. Preserve evidence before destructive actions within the deadline; hard budget cleanup cannot depend on an indefinitely blocked transfer.

For borrowed hosts, remove only task-owned services, workspaces and keys, leaving the host and existing work intact. For paid hosts, verify charge-ending state or exact absence and separately reconcile volumes/IPs/endpoints/snapshots. Acknowledgement is a receipt, not proof. Cleanup failures remain active cost incidents: preserve supervision, report exact IDs, current state/burn and manual remedy, retry bounded official paths, and avoid replacements while deletion is uncertain.

Report requested versus completed work, artifacts, source/runtime identity, validation, actual/estimated/unknown spend, cleanup/credential disposition and remaining incidents. Do not call the run complete with unverified billable resources.
