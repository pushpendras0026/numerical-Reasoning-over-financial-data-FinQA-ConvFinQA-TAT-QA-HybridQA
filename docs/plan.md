# Current plan — Gemini model migration v4

Updated 2026-11-06. The ordinary-WSL v3 smoke failed on the first token count:
HTTP 404, old model unavailable to new users. Zero completed requests and zero
model calls. The next live run uses gemini-3.8-flash and a fresh v4 directory.

| Task | Outcome |
|---|---|
| Read instructions, state, provider and contracts | Complete; actual file is Agents.md, uppercase AGENTS.md absent |
| Review official Google docs | Complete; keep v1beta countTokens/generateContent and JSON schema |
| Make compatible settings | Complete; low thinking replaces zero budget; remove sampling overrides and candidate count; retain output limit 2048 |
| Keep the comparison controlled | Same questions, seed, split, prompt/schema, three packers and 4000-token evidence caps |
| Preserve history | Original/v3 contracts, v3 registry and failed live directory retained and hash-checked |
| Version the model block | 21 new frozen_v4 contracts; contracts_v4 registry; fresh prepared/mock/live paths |
| Update downstream configs | All Gemini base configs including diagnostics/full runs and blocked HybridQA select 3.8 |
| Local checks | 52 tests; structured output, counting, cache separation, resumption; nine-row fake-HTTP smoke and replay |
| Account gate | New model/date attestation required; private .env untouched; no paid fallback |
| Live verification | Pending ordinary-WSL user execution after account checks; no live APIs called by agent |

Sources and exact setting changes: [gemini-migration-v4.md](gemini-migration-v4.md).
Commands: [final-testing.md](final-testing.md). Local evidence:
`artifacts/model_migration_v4/`. Historical model and data plans remain under history.

Next, inspect the project owning the key in AI Studio: Free tier, disabled/unlinked
billing, exact model access, and enough request/token quota. Only then set the new
model and its current UTC-date attestation privately, and run:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/p_2626/bigdata-env/bin/python -m nrqa.experiment run experiments/frozen_v4/smoke.json artifacts/live_smoke_v4 --mode live
```

After a completed smoke, replay it, score it, and manually trace a real result.
Then continue v4 pilots/full runs/diagnostics in final-testing.md. Use only v4 live
outputs for the new comparison; keep per-dataset scores separate. Spark acceptance
and the full-dev overlap audit are already saved, with scope limits in state.md.
HybridQA stays blocked until its genuine linked corpus is acquired and validated;
no inference contract is fabricated. Report accuracy/uncertainty/latency and TeX/PDF
acceptance remain pending. Never overwrite a contract after code or input changes.
