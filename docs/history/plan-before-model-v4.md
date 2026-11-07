# Current implementation and validation plan

Updated 2026-11-06. The saved research design remains unchanged. This milestone
reconciles real data discovery and reader assumptions without inference APIs,
package installation, raw-data changes or overwriting frozen contracts.

| Task | Outcome |
|---|---|
| Read instructions/state/testing/readers/configs | Complete; actual instruction file is `Agents.md`, uppercase file absent |
| Inspect both supplied locations | Complete; HybridQA questions present, linked corpus absent; all MultiHiertt splits present |
| Correct data paths | Relative sibling MultiHiertt sources; configurable HybridQA corpus candidates and explicit root overrides |
| Reconcile real HTML and IDs | Multi-row td headers, unit/section handling, merged-coordinate aliases, explicit table/text markers |
| Preserve label boundary | Questions/HTML/text only; label/description mutation tests on real records pass |
| Validate every available split | All 10,440 MultiHiertt records checked; all 69,611 HybridQA questions inventoried and corpus-blocked explicitly |
| Check annotations | All gold table/text references resolve; 61 stale cached description coordinates reported with IDs |
| Check official formats/scorers | Numeric program answer serialization fixed; full-ID abstention/export checks and real arithmetic/span round-trips |
| Run tests | 50/50 pass, including six new real-data/path/scoring regressions |
| Version contracts | 21 active v3 freezes; all 18 prior files hash-preserved; no fabricated HybridQA inference contract |
| Run requested local/delivery checks | Completed; delivery status explicitly retains the HybridQA external blocker |
| Update docs and draft readiness | Current state, README, testing/acquisition instructions and report input-readiness text updated |

The original broader implementation is retained: shared retrieval, three packers,
validated answer tools, predicted conversation state, two existing providers,
durable request/cache ledger, official scorers, Spark/Python preparation, experiment
aggregation and report source. The unit suite still covers those components.

Next actions are independent of this completed local reconciliation:

1. Run `scripts/validate_local.py` in ordinary WSL to confirm the same mounted files.
2. Acquire the actual HybridQA linked corpus as documented in `acquisition.md`.
   Verify every assigned table and nonempty passage, then freeze a new HybridQA
   contract under `experiments/frozen_v3` without replacing any existing contract.
3. Inspect the 61 unused cached-description mismatches if reproducing the upstream
   description-based system; our raw-HTML inputs retain all records and flag the
   metadata issues. Do not invent cells or patch raw JSON.
4. Continue later acceptance in `final-testing.md`: Spark correctness/resources,
   overlap audit, account/model gate, live smoke/replay, pilot and feasible per-dataset
   runs, component diagnostics, official scoring, measured report updates and TeX/PDF.

The next command from `final` is:

```bash
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python scripts/validate_local.py
```

Old milestone plans are preserved under `docs/history`. Existing historical
freezes and run ledgers must not be repurposed under new code. Current runnable
contracts and historical checksums are recorded in `experiments/contracts_v3.json`.
