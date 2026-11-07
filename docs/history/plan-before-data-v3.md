# Delivery implementation plan and completed checks

Updated 2026-11-06. This replaces obsolete milestone stop instructions, preserved
under `docs/history/`. Current authorization is implementation and local checks
through delivery preparation, **without live inference or large experiments**.
The saved proposal remains the working design; concrete adjustments are recorded
in `implementation.md`.

| Order | Task | Implementation status | Acceptance evidence / limit |
|---|---|---|---|
| 1 | Read project documents and inspect current code | Complete | Actual `Agents.md` read; uppercase file absent; retained working FinQA/API components |
| 2 | Inspect HTTP 404 | Complete locally | Isolated saved failure to first token count; fixed diagnostic loss; cause/live access unverified |
| 3 | Six readers and reference firewall | Complete against available contracts | Four full dev readers checked; missing-data readers have documented-format fixtures |
| 4 | Shared retrieval and three packers | Complete locally | BM25, closure/deduplication/cycles, whole-fact budgets, neighbor control with measured gaps |
| 5 | Shared answer schema/tools | Complete locally | Extraction/list/count/arithmetic/aggregates/compare/select, question-grounded overlays, predicted-state program expansion |
| 6 | Dataset output/evaluator integration | Complete locally | All six official-function contract tests; zero/invalid/abstain/coverage behavior; hidden-label submissions exported |
| 7 | Provider execution infrastructure | Complete locally | Free gates, redacted errors, durable raw/parsed/usage/status records, retries/stops, exact model pins across resume |
| 8 | Python/Spark preparation and overlap | Implemented | Python joins/edges verified; local JVM startup blocked by socket EPERM; Spark equivalence still unverified |
| 9 | Freeze experiment configurations | Complete for available sources | 18 frozen configs, including smoke/pilots/ablations/direct/full dev/full test; missing data freeze after acquisition |
| 10 | Aggregation, bootstrap and plots | Implemented and mock-table checked | Rejects unlabelled mock/live mixing; no measured live rows/figures yet |
| 11 | ACL report draft | Source complete | Original style preserved; ten verified primary bibliography entries; compilation tools absent |
| 12 | Documentation and source delivery | Prepared | Ordered WSL instructions, package allowlist, local secret scan and file-hash manifest |

Checks are described with actual evidence in `state.md` and
`artifacts/implementation/`. The final local run passed **44/44 tests**. The suite includes the retained 23 tests plus
reader, tooling, official-evaluator, request-diagnostic, experiment-freeze,
resumption, model-pin, hidden-submission and preparation checks.

Execution commands, in full, are in `final-testing.md`. The first command is:

```bash
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python -m unittest discover -s tests -v
```

Remaining external execution order: local acceptance → acquire missing inputs and
validate them → Spark reference comparison and resource measurements → overlap
audit → free-account/model gate → three-question live smoke and cached replay →
fixed 20-question three-method pilot → feasible dataset subsets/full splits →
component diagnostics/direct baselines → official evaluation and aggregation →
measured report updates → TeX compilation/PDF inspection → final bundle.

Do not run live steps from the agent during this implementation task. Do not
repeat the completed connectivity diagnosis. Preserve failed/uncertain ledgers
and inspect redacted details; do not switch the frozen model automatically.
