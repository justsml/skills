# Cost guards

Read this before a regression suite, scorer calibration, or optimization loop spends model calls.

- Bound the run first. Record the expected case count, model calls, and rough cost. Prove the path on a handful of cases before scaling up.
- Log token counts, call counts, model, platform, and cost with the dataset revision, candidate configuration, and scorer version.
- Retry rate limits, timeouts, 5xx responses, connection resets, and temporary dependency outages. Treat one uncertain retry as a diagnostic.
- Stop on authentication failures, malformed requests, schema violations, quota exhaustion, or consistently wrong scorer or candidate output.
- Use exponential backoff with jitter and a hard attempt limit. If an outage persists, record the blocked path and skip, substitute, or resume it later.
- Abort unbounded cost growth, flat or worsening results past the planned budget, repeated identical failures, or scorer gaming. Report what the run spent and why it stopped.
