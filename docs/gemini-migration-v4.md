# Gemini 3.8 Flash migration — 2026-11-06

The ordinary-WSL run in `artifacts/live_smoke_v3/manifest.json` stopped at
`POST /v1beta/models/gemini-2.5-flash:countTokens`: HTTP 404, NOT_FOUND.
The saved provider message says the model is no longer available to new users
and names `gemini-3.8-flash`. There were zero completed requests, zero generation
attempts and one token-count attempt. This explains this run; it does not prove
the cause of the earlier body-discarding failure in `docs/provider-404.md`.

## Official documentation reviewed

Google pages were consulted through public search on 2026-11-06. Direct page
opening returned an unsupported `text/markdown` error; indexed official text was
used instead. No authenticated model, counting or generation probe was made.
Some generic examples still show older parameters. The model-specific migration
checklist takes priority for the new model.

- [Model migration guide](https://ai.google.dev/gemini-api/docs/latest-model):
  names 3.8 Flash; remove temperature, top-p, top-k and candidate count; use a
  thinking level instead of a thinking budget. Minimal is unsupported.
- [GenerateContent support](https://ai.google.dev/gemini-api/docs/interactions-overview):
  Google recommends Interactions for new projects but still supports GenerateContent.
  We keep the existing Developer API and API-key header; no SDK or API migration.
- [Generation reference](https://ai.google.dev/api/generate-content) and
  [legacy text generation guide](https://ai.google.dev/gemini-api/docs/generate-content/text-generation):
  `POST /v1beta/models/gemini-3.8-flash:generateContent` remains the endpoint.
  REST uses `generationConfig.thinkingConfig.thinkingLevel`.
- [CountTokens reference](https://ai.google.dev/api/tokens) and
  [token guide](https://ai.google.dev/gemini-api/docs/tokens): counting remains
  model-specific, with `contents` and a `totalTokens` response. Keep
  `POST /v1beta/models/gemini-3.8-flash:countTokens` and the existing body.
- [Structured outputs](https://ai.google.dev/gemini-api/docs/structured-output) and
  [generation reference](https://ai.google.dev/api/generate-content): keep JSON
  MIME type and `responseJsonSchema`. Our object, array, bounds, enum and anyOf
  schema stays within the documented subset. Local validation remains required.
  The reference also advertises newer response-format fields; that alone does
  not require changing this existing compatibility route. Schema size/complexity
  and real provider acceptance still need the ordinary-WSL smoke.
- [Pricing](https://ai.google.dev/gemini-api/docs/pricing): Standard 3.8 Flash
  publicly lists free input and output (including thinking). This does **not**
  establish this key's project eligibility, model access or available quota.
  [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) directs users to
  their project's active limits in AI Studio. No billing upgrade is authorized.

## Exact setting changes

| Field | v3 | v4 | Reason |
|---|---|---|---|
| model | gemini-2.5-flash | gemini-3.8-flash | Old model rejected this account's counting request |
| temperature | 0 | omitted | Model-specific migration guide removes sampling overrides |
| topP | 1 | omitted | Same rule |
| candidateCount | 1 | omitted | Unsupported on Gemini 3 and later; response parser still requires one candidate |
| thinkingConfig | thinkingBudget: 0 | thinkingLevel: low | Zero budget is replaced; low is the lowest supported level |
| maxOutputTokens | 2048 | 2048 | Preserved |

No topK or provider seed was sent before; neither is added. The local selection
seed remains 2626. Thinking cannot be disabled as before, so this is a new model
comparison block. Low is a controlled choice to limit reasoning effort; it is
not a claim of equivalent reasoning, deterministic output, cost or accuracy.
The output limit can truncate thinking or the final JSON; incomplete output stays
a failure. We do not raise this limit based on gold answers or smoke performance.

All ordinary, dependency and length_matched rows use the same frozen settings.
Questions, IDs, exclusion lists, split/source/input hashes, prompt/schema, packers,
4000-token evidence caps and generation-attempt caps are unchanged. Evidence-only
counting still budgets the exact visible evidence serialization; input text counts
are separate and do not claim to include system/schema overhead. Actual new-model
tokenization can change which facts fit; no old token counts are reused.

## Version and account boundary

`experiments/contracts_v4.json` lists 21 new contracts in `experiments/frozen_v4/`.
The 18 original freezes plus all 21 v3 freezes remain historical and hash-checked.
`contracts_v3.json` and `artifacts/live_smoke_v3/` are unchanged. Active base configs,
including blocked HybridQA and unfrozen diagnostics, now select the new model.
HybridQA still has no inference contract because its evidence corpus is missing.

Use fresh `artifacts/prepared_smoke_v4/`, `artifacts/mock_smoke_v4/` and later
`artifacts/live_smoke_v4/`. No SQLite file is copied. Generation cache keys include
provider/model/version, settings and request; token-count keys include model identity
and text. Old run directories also reject a different contract. Legacy two-method
scripts are historical helpers, not the active three-method experiment commands.

Private `.env` was neither read nor changed during this migration. Before any live
run, the operator must inspect the project owning the actual API key, confirm
Free tier with billing disabled/unlinked, exact `gemini-3.8-flash` access and
nonzero request/token limits with enough headroom for the bounded smoke (nine
logical predictions, at most 27 generation attempts, plus counting requests).
Only then set `GEMINI_MODEL=gemini-3.8-flash` and
`GEMINI_FREE_TIER_CONFIRMED=gemini-3.8-flash:YYYY-MM-DD` using the current UTC date.
Replace an old model value explicitly; process environment overrides `.env`.
The old model's attestation cannot authorize this model. Never infer eligibility
from the public pricing table or metadata success. If free quota is absent, stop;
there is no paid fallback, billing upgrade or automatic model switch.

Local evidence is in `artifacts/model_migration_v4/`; see `docs/final-testing.md`
for outcomes and the next ordinary-WSL command. Mock output is not model accuracy.
