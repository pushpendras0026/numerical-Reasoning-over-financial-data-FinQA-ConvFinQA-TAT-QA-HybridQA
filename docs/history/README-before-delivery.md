# FinQA local and API integration milestones

## Live-access checkpoint — 2026-11-06 (current)

Selected **Gemini Developer API, `gemini-2.5-flash`**. The user confirmed the
owning project's Free tier, disabled/unlinked billing and sufficient model quota
in the console. Saved today's model-scoped attestation in ignored `.env`;
this is operator evidence, not independent verification. The newly supplied
Gemini secret was moved out of `.env.example` without printing it. The example
has empty credential fields and a nonsecret frozen model setting. Both provider
keys exist locally; no secret matches were found outside `.env` and `api.txt`
in the workspace scan (Git history is unverified). **The exposed OpenAI key is
not revoked, as confirmed by the user; revoke it in the provider console.**
Permissions and ignore rules do not undo exposure. OpenAI remains blocked.

Network evidence: DNS returns `EAI_AGAIN` (`-3`) for Google, OpenAI and
`example.com`; verified HTTPS stops at that same resolution failure. More
fundamentally, local TCP and UDP socket creation returns `PermissionError`,
`EPERM` (`1`) in the agent environment. No proxy variables are present.
Default TLS trust loads 145 CA certificates, but no remote handshake occurred:
certificate validity is untested. Kernel is WSL2; ordinary WSL behavior is now verified below. This establishes an execution-environment socket restriction, not
proof that WSL or the internet is down. No restriction or TLS check was bypassed.
Redacted evidence: `artifacts/access_diagnostics/{network,access_review}.json`.
No authenticated request, token count or generation was dispatched this session.

The user has now supplied ordinary WSL diagnostics: TCP/UDP socket creation
succeeds, all three hosts resolve, and verified HTTPS returns Google 404,
OpenAI 421 and example.com 200. Root-path HTTP errors establish transport only,
not authentication or model access. This isolates the failure to the agent's
execution environment. The terminal loads 120 CA certificates; its verified
HTTPS succeeds. Saved evidence: `artifacts/access_diagnostics/ordinary_wsl_network.json`.
No need to repeat the public checks.

**Next action:** execute the existing six-request Gemini smoke once in the
ordinary WSL terminal, which has working connectivity. The agent cannot execute
network requests in that terminal or bypass its own socket restriction.

```bash
cd /home/p_2626/BigDataEndSem/final
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python scripts/run_api_finqa.py
```

Return the terminal summary; never include `.env` or keys. The script uses the
existing output/cache and checks authenticated model access before inference.
If it stops for quota or uncertain completion, preserve the checkpoint and
report the stop; do not blindly retry or switch providers.

Do not run inference if the connectivity check fails. The entrypoint performs
authenticated exact-model/method checks before counting or generating. The
attestation expires each UTC day; renew only after checking the same project.
Preserve cache.sqlite; quota/ambiguous/inflight stops require inspection rather
than an automatic rerun. Completed requests are reused. After a completed run,
a second invocation verifies six cache hits without duplicate generation.
Questions, instructions, evidence cap, settings and retry policy are unchanged.

Current [Google API-key setup](https://ai.google.dev/gemini-api/docs/api-key)
uses `x-goog-api-key`; [models.get](https://ai.google.dev/api/models) checks
availability. Google's [pricing](https://ai.google.dev/gemini-api/docs/pricing)
contains a 2.5 Flash free tier, but
[current availability notices](https://firebase.google.com/docs/ai-logic/faq-and-troubleshooting)
restrict deprecated Gemini 2.5 models to previously active projects and warn of
routing changes from December 1, 2026. Older indexed deprecation/model pages
conflict; authenticated access and observed resolved-model checks remain
necessary. Do not silently replace the frozen model. Public documentation was
reviewed through web search and the live official Firebase page; direct Google
AI page opens failed with unsupported text/markdown errors.

Validation: **23/23 tests pass**, including safe Gemini `.env` loading, process
overrides, gates, packed-evidence isolation and mock resume. The bounded network
helper was syntax checked. **Zero real predictions, usage, latency or official
live scores exist**, so no real prediction can yet be explained. Test/mock scores
are engineering checks only. Stop at this access checkpoint; no broader study.


Run with the existing environment, without installation:

```bash
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python scripts/run_local_finqa.py
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python -m unittest discover -s tests -v
```

The runner uses ten fixed FinQA **training** examples. All predictions are
**handwritten test fixtures, never model results**. They were authored with
training labels visible to test the execution/scorer contract. The runner resolves
the handwritten operand selectors against prediction inputs only; it does not
read reference programs to generate predictions. Ambiguous repeated values use
the first source occurrence, suitable only for these engineering fixtures.

`src/nrqa/core.py` contains shared records, lexical overlap retrieval and packing.
`finqa.py` uses an input allowlist and returns references separately.
`execute.py` validates grounded spans and runs Decimal operations without eval.
`evaluation.py` checks exact ID coverage and loads the unchanged official local
FinQA scorer. NumPy, SymPy and tqdm are needed by that scorer and were verified
in the existing environment. Core preparation otherwise uses the standard library.
The old implementation was inspected; no code from its combined input/label
records was reused.

Artifacts in `artifacts/local_finqa/` include prediction inputs, separate
references, packing logs, grounded fixture plans, traces, official outputs,
metrics and source/fixture/scorer hashes. Reference-bearing artifacts belong
only to evaluation. Do not send the whole artifacts directory to a model.

Both retrieval variants use 4,000 **estimated** evidence tokens. Counts cover
serialized evidence including IDs and source metadata, using ceil(UTF-8 bytes/4),
not a model tokenizer. Packing admits whole candidates, with no string truncation.
Dependency packing recursively closes required headers/unit mentions, deduplicates
shared nodes and rejects bundles that exceed the cap. Ordinary packing includes
readable immediate headers inline. Unit paragraphs are conservative inferred
dependencies with uncertainty; no table hierarchy or unit scale is invented.
Linked and conversational dependencies can use the same adjacency interface;
FinQA has neither and this milestone does not implement those readers.

Execution fixtures use a separately disclosed 100,000 estimated-token cap to
include the complete supplied context. Their scoring tests compiler/scorer
compatibility, not retrieval coverage or QA performance. Extraction is locally
supported but has no official FinQA program export here; no identity operation
is fabricated. Table aggregates and the remaining shared reasoning capabilities
are later work.

For example, the ADI question gets stable paragraph/cell IDs tied to its source
file and record position. Its `pre_text[1]` retains “100 basis points” and “3.8
million” with offsets. Retrieval ranks supplied facts; each packer logs admitted
and dropped candidates. The handwritten fixture grounds 100 and 3.8 in input
spans, computes 100/100, then 3.8 divided by that result. Execution emits 3.8 and
the FinQA operation tokens. Only the scorer then reads reference programs and
answers. This example demonstrates the contract, not a discovered answer.

All six datasets remain in the evaluation plan; see `docs/state.md`. Actual
coverage is ten FinQA training fixtures and zero model runs. No accuracy
improvement, sampled development score or full-dataset result is claimed.

## One-provider API milestone (2026-11-06)

The model path is `scripts/run_api_finqa.py` → `model.request` → `Gemini` →
`parse_and_execute` → official scorer. Its last serialization boundary accepts
only the question and selected evidence (`id`, `raw`, `unit`). The executor gets
that same packed evidence. It never imports the full-context fixture runner.
Tests mutate gold fields and the full document, and reject a reference to an
unselected fact. No reference label repairs a prediction.

Implemented: provider-independent protocol, Gemini REST adapter, JSON schema
and local validation, SQLite request/cache ledger, raw/parsed/error/usage/latency
records, bounded retries and restart reuse. No packages were installed.

```bash
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python -m unittest discover -s tests -v
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python scripts/run_mock_api_smoke.py
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python scripts/run_api_finqa.py
# Run the last command again to reuse completed requests.
```

Verified locally: 17 tests pass after the authentication review. The saved mock run has six abstention fixtures
(three fixed dev questions × two packers). The unchanged official scorer gives
0/3 execution and 0/3 program checks for each mock variant, as expected for
abstentions. Restart reused all six requests with zero new generation calls.
These are transport/contract tests, **not model accuracy results**. Mock token
counts, usage and latency are synthetic/local. See
`artifacts/api_mock_finqa/mock_verification.json` and `results.json`.

The latest invocation stopped before inference: **0 live calls and no live scores**.
No Gemini key is configured in the process environment, and account eligibility
has not been established. No inference, countTokens or authenticated model
metadata request was sent. The live blocked manifest remains in
`artifacts/api_finqa/`; mock responses remain separately in `artifacts/api_mock_finqa/`.

### Minimum authentication and free-only eligibility (2026-11-06)

This adapter uses the **Gemini Developer API**, not Vertex AI:
`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash`.
Google's [REST authentication reference](https://ai.google.dev/api) specifies
`x-goog-api-key`. The only authentication variable this implementation needs is
`GEMINI_API_KEY`, containing a Gemini Developer API key from AI Studio.
`GEMINI_MODEL` is optional and defaults to the already frozen `gemini-2.5-flash`;
other model names fail closed. No automatic model switching is implemented.
The Gemini entrypoint now reads whitelisted literal assignments from ignored `.env`; process environment overrides them. `api.txt` is not loaded.
Set secrets locally through your shell or secret manager; do not paste them
into conversation, commands that echo them, or artifacts.

Project numbers, key IDs and OAuth tokens are **not inference requirements**.
The previous implementation required them for two administrative checks:
[GetKeyString](https://docs.cloud.google.com/api-keys/docs/get-info-api-keys)
retrieved the configured key resource (project number/key ID, OAuth scope
`cloud-platform`, permission `apikeys.keys.getKeyString`) to bind it to a project;
[getBillingInfo](https://docs.cloud.google.com/billing/docs/reference/rest/v1/projects/getBillingInfo)
read that project's billing state (project identifier, OAuth read scope,
`resourcemanager.projects.get`). These optional audits do not establish remaining
model quota. They are no longer invoked or required by this smoke runner.

Google's [pricing table](https://ai.google.dev/gemini-api/docs/pricing#gemini-2.5-flash)
lists standard 2.5 Flash input and output as free on the Free Tier. This is
model-level policy only, **not proof of this account's eligibility**. The
[billing guide](https://ai.google.dev/gemini-api/docs/billing) and
[rate-limit guide](https://ai.google.dev/gemini-api/docs/rate-limits) explain tiers
and direct users to AI Studio for their actual limits.

Minimum console check, using the same account and project that own your key:

1. Open [AI Studio API keys](https://aistudio.google.com/api-keys), identify your
   key's owning project, and confirm its plan/billing tier is **Free**. In that
   project's [Cloud Billing](https://console.cloud.google.com/billing) view,
   confirm billing is disabled/no billing account is linked. Do not enable it.
2. Open [AI Studio rate limits](https://aistudio.google.com/usage?tab=rate-limit),
   select that same project, and inspect **gemini-2.5-flash**. Confirm access is
   available, RPM/TPM/RPD limits are nonzero, and usage leaves request/token
   headroom. Six logical generations are needed; the maximum is 18 attempts.
   This cannot guarantee capacity at dispatch; any 402/429 checkpoints and stops.
   A zero/missing quota, eligibility warning, or request to enable billing blocks
   this experiment. Do not substitute another model.

After completing those checks today, set the nonsecret policy confirmation
`GEMINI_FREE_TIER_CONFIRMED=gemini-2.5-flash:YYYY-MM-DD`, using today's **UTC**
date. This is an operator attestation about the project owning the configured
key, not a Google token or an independently verified account status. It expires
by date and must be renewed after changing keys/projects. Leave it unset if
anything is uncertain. `.env.example` lists only the key, optional frozen model,
and this policy confirmation.

On success, preflight performs authenticated
[models.get](https://ai.google.dev/api/models) and requires the exact name,
version, and generateContent/countTokens support. Metadata availability alone
never opens the free-use gate. The manifest labels the account evidence as
`operator_console_confirmation`, with `independently_verified=false`. No paid
fallback, billing enablement, resource creation or top-up path exists. This
console-based gate relies on accurate operator confirmation; it does not monitor
later billing changes remotely.

Credential audit: `api.txt` was examined only locally without printing its
contents or sending it to inference. It contains an OpenAI-style secret, no
recognizable Google API key, and is excluded by `.gitignore`. Exact credential
strings found there did not occur in checked source, tests, scripts, docs,
experiments or artifact files. The `.git` directory is empty and `git ls-files`
fails: **tracking/history cannot be verified**. Ignore rules do not prove a file
was never committed. No observed credential exposure was found in those checked
files; prior history and other locations remain unaudited. No credential was
copied into artifacts. See `artifacts/api_finqa/access_review.json`.

### Frozen smoke protocol and artifacts

`experiments/finqa_api_smoke.json` freezes the first three FinQA dev source IDs:
`V/2008/page_17.pdf-1`, `C/2017/page_328.pdf-1`, `DVN/2007/page_58.pdf-2`.
Each runs ordinary then dependency-preserving packing. Model, prompt/schema,
4,000 evidence-token cap, temperature 0, top-p 1, one candidate, thinking budget
0 and 2,048 output-token limit stay fixed. At most three attempts/request and
18 generation attempts total are allowed. No other dataset is integrated.

Live packing uses Gemini `countTokens` on the **exact serialized evidence** sent
to the model, with memoized counts. User-input counts are recorded separately;
they exclude system/schema overhead. Actual prompt/output/thinking usage is
saved from `usageMetadata`. Offline preparation retains the old explicitly
estimated UTF-8-bytes/4 accounting over full fact metadata. Mock counts do not
establish real tokenizer correctness. Token-count requests have a separate
1,000-call limit per invocation; metadata uses one models.get per successful preflight.

Cache keys cover provider/model/version, instructions, JSON schema, question,
selected evidence and generation settings. The ledger commits dispatch before
network access and raw responses before parsing. Completed/invalid outputs are
reused; parsing never triggers a repair call. Transient 5xx errors receive at
most two retries with jitter and bounded waits respecting Retry-After. A wait
above 60 seconds ends retries. Every 402/429 stops immediately with progress
saved. Quota/ambiguous/inflight records remain stopped on restart; inspect them
before starting a deliberately new run after quota reset. A timeout can have
completed remotely, so it is never retried automatically. One process owns each
ledger; a file lock prevents concurrent duplicate dispatch.

Saved files include `manifest.json` (configuration, source/scorer hashes, model,
counts, gate and stop reason), `prepared_inputs.json` (estimates only),
`current_input.json` (last exact live input), `results.json` (packing, request,
raw response, parsed plan, execution, attempts, latency and usage),
`cache.sqlite` (durable request and token-count records), `metrics.json`, and
per-variant official prediction files. Official references are written only in
the evaluation phase after all inference completes. A stopped partial run has
no completed paired score. Server-reported resolved model drift stops scoring.
Re-running a completed experiment reuses cached requests and recounts no cached
text; free-access preflight still runs. Do not delete the ledger to recompute
scores.

For an easy real-data example, the first question asks for American Express's
average payment per transaction. Both estimated preparation bundles contain
payment volume **637 billion** and **5.0 billion** transactions, with labels.
Dividing those input values gives **127.4 per transaction**. This is a manual
illustration of the needed operation, not a model prediction or a gold-driven
repair. Ordinary packing puts labels inline; dependency packing keeps shared
labels as separate selected facts. Only a live run can establish what the model
actually predicts. Three questions cannot establish an architectural gain.


## OpenAI smoke route (Gemini retained)

The user authorized an explicit OpenAI alternative. The Gemini adapter, script,
settings and artifacts remain available for a later Gemini key. There is no
automatic provider fallback or cross-provider score comparison.

```bash
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python scripts/run_openai_finqa.py
```

This route reads `final/.env` as literal assignments without shell execution;
process settings override file settings. Only `OPENAI_API_KEY`, legacy alias
`OPEN_AI`, `OPENAI_MODEL`, and `OPENAI_FREE_CREDITS_CONFIRMED` are accepted.
The key uses [Bearer authentication](https://developers.openai.com/api/reference/overview).
No project number, key resource ID or separate OAuth token is required.
Model selection is explicit: set `OPENAI_MODEL` to the intended model ID.
There is no default model or silent substitution. Unsupported API settings or
models fail as recorded errors rather than triggering a different model.

The existing **$0 spending policy remains in force**. An API key and successful
models.get do not establish free credits. In the organization/project owning
that key, check [Billing](https://platform.openai.com/settings/organization/billing/overview)
for sufficient **unexpired free API credits** for the entire bounded smoke run,
and confirm there is no paid payment method or automatic recharge. Check
[Limits](https://platform.openai.com/settings/organization/limits) for model access
and request/token quota. A purchased balance is not free-credit evidence.
OpenAI documents [free API credits for eligible subscribers](https://developers.openai.com/api/docs/guides/chatgpt-api-credits),
but account eligibility and the available grant must be checked in the console.
Do not buy credits, enable paid billing or change subscriptions for this test.

After those checks, set the nonsecret
`OPENAI_FREE_CREDITS_CONFIRMED=MODEL:YYYY-MM-DD` for today's UTC date and the
exact configured model. This is operator attestation, not independent billing
verification. It must be renewed when keys/accounts change. Without it no
metadata, count or generation request is dispatched. The adapter subsequently
checks authenticated model availability using models.get. No undocumented
billing endpoint or elevated admin credential is used.

OpenAI uses the same three fixed questions, both packers, unchanged instructions
and local answer-plan schema, a 4,000 evidence-token cap, temperature 0, top-p 1,
one response, 2,048 output tokens, three attempts/request and 18 attempts total.
Gemini's thinkingBudget field is not sent to OpenAI. Both OpenAI packers use
identical settings; models must support those settings. Responses
[JSON mode](https://developers.openai.com/api/docs/guides/structured-outputs)
provides JSON syntax; the existing local validator enforces the plan contract.
This is distinct from Gemini's transport schema enforcement. No gold fields or
reference programs enter inference. The output path is
`artifacts/api_openai_finqa/`, separate from Gemini and saved mocks.

Token counts use [responses/input_tokens](https://developers.openai.com/api/reference/resources/responses/subresources/input_tokens/methods/count)
on the evidence-only string, including request framing. This conservative count
is not a raw-string tokenizer count. User-text counts also include framing;
actual input/output usage comes from each response's `usage`. Raw responses,
resolved `model`, execution, latency, attempts and official scoring use the shared
ledger. Completed requests are reused; quota errors checkpoint and stop.

Current verification: **22/22 tests pass**, including the six-request OpenAI mock
smoke and resume with six cache hits and zero new mock generations. Mock outputs,
usage and latency are synthetic, saved only in test temporary directories. The
real OpenAI entrypoint stops at `missing_configuration:OPENAI_MODEL`; no generation/token-count requests or live scores exist. The key is present, but free-credit status remains
unconfirmed. No method was tuned or improvement claimed.

Credential incident: the key had been placed in `.env.example` and was exposed
in tool output when that example was read. It has been moved to ignored `.env`
(mode 0600), and the public example contains only empty values. Revocation by the user is required before any OpenAI use. File permissions do not undo prior exposure. The same key also exists in the pre-existing ignored `api.txt`; no other exact
key matches were found in checked source or artifacts after relocation; tool-output exposure cannot be undone here, and Git history remains
unauditable. Do not print or share `.env`. See
`artifacts/api_openai_finqa/access_review.json` for the redacted status report.

A separate read-only authentication probe attempted `GET /v1/models`, which
needs no inference and makes no credit eligibility claim. It failed to connect
with `ambiguous_transport`; key validity and hosted model access therefore remain
unknown. This was one metadata attempt, zero successful metadata responses and
zero inference calls. See `artifacts/api_openai_finqa/access_probe.json`.
