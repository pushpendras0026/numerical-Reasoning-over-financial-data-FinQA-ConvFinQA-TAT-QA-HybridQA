# Current project state — Gemini model migration v4

Updated 2026-11-06. The active model is now **gemini-3.8-flash**. The API remains
Gemini Developer API v1beta: countTokens and generateContent with API-key auth
and the existing structured JSON schema. No live APIs were called by the agent.
Private `.env` was not read or changed; no account attestation was set.

The ordinary-WSL failed run is preserved in `artifacts/live_smoke_v3/`.
Its saved 404 says gemini-2.5-flash is no longer available to new users and names
3.8 Flash. It stopped at countTokens: one count attempt, zero completed requests,
zero model calls. Metadata success did not establish counting/generation access.

All three methods share `maxOutputTokens: 2048` and
`thinkingConfig: {thinkingLevel: low}`. The required migration removes temperature,
topP and candidateCount and replaces thinkingBudget 0 with low thinking. No topK
or API seed is added. Questions, selection seed, IDs/exclusions, source/input hashes,
prompts/schemas, packers and evidence/generation caps are unchanged. New-model
reasoning cannot be disabled; this is a new controlled block, not equivalent
old-model decoding. [Exact changes and official sources](gemini-migration-v4.md).

`experiments/contracts_v4.json` lists 21 active `experiments/frozen_v4/` contracts
and hashes all 39 historical contracts. `frozen_v3`, the original `frozen`, the v3
registry and every file in the failed live directory retain their bytes. All
Gemini base configs now select 3.8, including downstream diagnostics/full runs and
blocked HybridQA. HybridQA still has no inference contract: its real linked corpus
is absent. Data readers and raw datasets were not changed.

Local check evidence in `artifacts/model_migration_v4/`:

- 52 unit/integration tests passed. Fake HTTP checks exercise program/direct JSON
  serialization, valid/invalid structured parsing, exact counting body/endpoint,
  model-separated prediction/count caches, crash/resumption and account gates.
- All 21 v4 freezes were compared against v3: only the model changes in config;
  IDs, inputs, sources, prompt/schema and selection metadata match exactly.
- Fresh `artifacts/prepared_smoke_v4/` has nine rows. Fake-HTTP Gemini
  `artifacts/mock_smoke_v4/` has nine completed logical rows across three methods.
  First run: nine generations, no prediction cache hits. Replay: nine hits,
  zero new generations and zero new token counts. All evidence caps hold.
  Mock abstentions retain all three questions in each method's scoring denominator.
  Counts, usage and outputs are synthetic; these are not accuracy results.
- Full local data validation and delivery checks retain the external HybridQA
  blocker. Preserved-file hashes and code/source/input contract checks are saved.
- The new live v4 directory has not been created; no prior predictions or token
  counts were copied. The cache keys already separate model identity/settings.

Public Standard pricing lists free 3.8 input/output, including thinking; this does
not establish this account's eligibility. The operator must check the key's owning
project in AI Studio for Free tier, disabled/unlinked billing, exact 3.8 model access
and sufficient nonzero request/token quota. Then explicitly set
`GEMINI_MODEL=gemini-3.8-flash` and
`GEMINI_FREE_TIER_CONFIRMED=gemini-3.8-flash:YYYY-MM-DD` using the current UTC date.
An old-model attestation cannot pass. If free access is unavailable, stop. The $0
ceiling, no-paid-fallback rule and no automatic model/provider switch remain.

Exact next ordinary-WSL command, from `/home/p_2626/BigDataEndSem/final`, after
that account check:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/p_2626/bigdata-env/bin/python -m nrqa.experiment run experiments/frozen_v4/smoke.json artifacts/live_smoke_v4 --mode live
```

Follow [final-testing.md](final-testing.md) for replay, scoring and later v4 runs.
Live schema acceptance, actual tokenization, model outputs and accuracy remain
unverified until that run. Report results, uncertainty, ablations, latency and
TeX/PDF acceptance remain pending. No packages were installed.

Earlier verified data counts, the small Spark acceptance/resource evidence and
full-dev overlap audit remain valid in scope, with all caveats recorded in
[the preceding state](history/state-before-model-v4.md). Those input-only artifacts
were not changed or presented as new model measurements. The overlap artifact's
old config hashes refer to the preserved v3 configs inside frozen_v3; active base
config hashes changed with this model migration. Do not claim they match the new
base files. HybridQA, hidden-test scoring and report compilation remain blocked
or pending as documented there.
