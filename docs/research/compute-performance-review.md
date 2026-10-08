# Remote compute and performance helpers: final review

Reviewed 2026-10-07. Scope: both new skill workflows, project policy/accounting, performance experiment decisions, web guidance, executable helpers, runtime selection, local documentation links and package version consistency.

## Consequential findings fixed

- **Budget warnings could miss a small overrun:** six-significant-digit display rounding preceded the run-ceiling comparison. Both helpers now compare the unrounded final upper bound plus cleanup reserve; a regression case proves a displayed $7.50 forecast still warns for a true value above $7.50.
- **Malformed budget configuration could weaken visibility:** omitted fields could be treated as unspecified in the Node implementation. Both implementations require explicit fields, with null for unspecified limits and zero for no spend.
- **Unknown project rates obscured hourly headroom:** scoped status still checks every project-owned live resource, and now explicitly warns when unknown rates prevent assessing the aggregate ceiling.
- **Runtime conversion could conceal bad evidence:** Node refuses non-finite calculated JSON instead of allowing JSON.stringify to convert it to null. It rejects non-decimal CLI inputs and impossible calendar dates. Python uses the same portable timestamp form and strict numeric schema version.
- **Tiny log differences changed diagnostic warnings:** both comparators use a small log-ratio spread tolerance for effectively identical paired ratios. Seeded bootstrap draws match Python's integer-seeded MT19937 stream; comparison results are tested with a 1e-10 numeric tolerance. Preserve the selected runtime throughout an experiment; gate-boundary uncertainty is not a reason to change runtimes.

## Compatibility and evidence

Node 20+ and Python 3.10+ implementations are independent and need no packages or network access. Bash 3.2+ entry points choose compatible Node first, then Python. These are dispatchers, not Bash-only statistical implementations. Selection occurs before running a helper; a validation failure never triggers fallback. Tests cover paths with spaces, Python-only environments, neither runtime available, and preservation of decision exit codes.

Validated six skill metadata contracts, 21 evaluator tests, 59 offline contract fixtures, 12 Node/Bash helper test groups and 21 Python helper tests. Cross-runtime parity ran rather than being skipped. Local Markdown links, shell syntax, version alignment and diff whitespace passed. Tests are offline synthetic evidence: no paid resources, provider authentication, browser sessions, live model routing or end-to-end tuning were exercised. No additional critical/high issue was identified in this review scope.

The existing eval-expert difference between Claude implicit activation and Codex manual invocation remains an explicitly documented review item; this change does not alter that skill's activation contract.
