# HTTP 404 audit

Historical audit of the earlier failure. The later ordinary-WSL v3 failure saved
a provider message and is now addressed by the explicit
[Gemini migration v4](gemini-migration-v4.md). Its old-model directory is preserved.

Inspected the actual runner, transport, Gemini and OpenAI paths, configuration
loading and saved `artifacts/api_finqa/manifest.json` on 2026-11-06. No live
provider requests or repeat connectivity diagnosis were made during implementation.

The saved manifest records authenticated Gemini model metadata success
(`version=001`, required methods present), zero generation attempts, and one
token-count attempt before `http_404`. The inference was therefore stopped at
counting, not a failed model prediction. The old handler discarded response
bodies; there are no retained provider message/status/request-ID details from
which to identify a more specific cause. This is not proof of an invalid key,
missing model, or working generation access.

Current construction is the documented Developer API shape:

- GET `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash`
- POST the same path plus `:countTokens`
- POST the same path plus `:generateContent`
- `x-goog-api-key` header; model names are validated path segments, not arbitrary URLs.

Sources: official [models reference](https://ai.google.dev/api/models),
[countTokens reference](https://ai.google.dev/api/tokens),
[generateContent reference](https://ai.google.dev/api/generate-content), and
[troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting).
Public search exposed the official endpoint forms, but direct Google page fetches
failed with unsupported `text/markdown` in the documentation tool. No authenticated
metadata/counting/generation probe was used to resolve the uncertainty.
There is no evidence justifying an API-version or frozen-model substitution.

Implemented correction: diagnostic loss is fixed. HTTP failures retain a bounded
allowlist of provider status/code/type/param/message, HTTP method/status, endpoint
path, host, stage and request ID. Credential header values, recognizable secret
patterns, URLs and project identifiers are redacted; non-JSON bodies are discarded.
Errors survive preflight, counting, dispatch, and resumption through manifest/ledger
records. 402/429 stops immediately. Failed generation is cached; uncertain dispatch
is never automatically repeated. The historical attempt could not have a new body
recovered. Live access remains **unverified**.

OpenAI was retained. Official [token-counting guidance](https://developers.openai.com/api/docs/guides/token-counting)
and [Responses migration documentation](https://developers.openai.com/api/docs/guides/migrate-to-responses)
were fetched. The latter describes ordered message, reasoning and tool-call items;
response parsing now tolerates reasoning metadata before one completed assistant
message, rejects tools/refusals/incomplete content, and keeps actual usage.
The existing model/settings are preserved, with no fallback for incompatible models.
The earlier exposed OpenAI credential must be revoked/replaced before that optional
route is used; no OpenAI live experiment is prepared as the default.
