# Engineering diagnostic, not a completed experiment

Prepared offline from v5 diagnostics code with a small versioned configuration extension. No live requests executed. All v4 artifacts and the uncertain ledger are retained; do not resume or copy them.

This is a fresh attempt. The earlier request may have executed remotely. This diagnostic does not resolve that uncertainty, even if successful.

The diagnostic selects existing smoke question V/2008/page_17.pdf-1 and ordinary packing. Model, instructions, schema, evidence cap and generation settings match frozen v5 smoke. New frozen v6 contracts record generation_attempts=1 and response_timeout_seconds=180. Defaults remain three attempts and 60 seconds. The timeout is urllib's finite socket timeout (connection/header wait and body reads), not a total wall-clock deadline. Metadata and token counting remain necessary and are distinct from the single generation attempt.

Free-only verification and the existing dated account confirmation remain required. Keep billing disabled and verify available model free quota in the account console; use the existing GEMINI_FREE_TIER_CONFIRMED convention. No credential values belong in logs.

Run in ordinary WSL from /home/p_2626/BigDataEndSem/final:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/p_2626/bigdata-env/bin/python -m nrqa.experiment run experiments/frozen_v6/diagnostic.json artifacts/engineering_diagnostic_v6 --mode live
```

The output directory is already prepared offline with zero calls. Manifest and SQLite retain redacted diagnostics; successful raw output is checkpointed in SQLite before parsing and results.json retains the returned prediction. A failed HTTP response retains redacted error information, not an unredacted body. Do not repeat after failure or uncertainty. Inspect manifest, results and ledger before continuing; success requires one completed generation with a saved response and no stop/error, with stable model identity.

Only after successful review, run the full nine predictions in a separate fresh directory:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/p_2626/bigdata-env/bin/python -m nrqa.experiment run experiments/frozen_v6/smoke.json artifacts/live_smoke_v6 --mode live
```

All nine use one frozen contract, one attempt each, and the 180-second socket timeout. The diagnostic and smoke have different selection/contracts: do not aggregate, copy caches, or substitute the diagnostic prediction into smoke results. Neither command resolves historical uncertainty.

Focused offline checks: 8 diagnostic tests and 13 API mock tests passed. Both new contracts froze successfully and diagnostic preparation made zero model calls. Historical frozen contracts are retained and intentionally cannot run under changed source hashes.
