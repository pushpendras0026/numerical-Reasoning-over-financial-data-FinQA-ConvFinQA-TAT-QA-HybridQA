# Project state

## Ordinary WSL evidence — 2026-11-06 (latest)

User returned the bounded diagnostic output from ordinary WSL. Both socket
types succeed; DNS resolves Google/OpenAI/example.com (16/4/4 addresses);
verified HTTPS returns 404/421/200 respectively. No proxies configured;
120 trusted CAs load. HTTP errors at API root paths do not establish key or
model validity. Agent EPERM socket failures are isolated to its execution
environment; no general WSL DNS/TLS fault is supported. Evidence saved as
`artifacts/access_diagnostics/ordinary_wsl_network.json`, attributed to the user.
Updated access_review.json and README. No extra network retry or inference
performed here; real responses, token usage, scores and walkthrough still pending.

Next action: run once in ordinary WSL:
`cd /home/p_2626/BigDataEndSem/final` then
`PYTHONPATH=src /home/p_2626/bigdata-env/bin/python scripts/run_api_finqa.py`.
Gemini gemini-2.5-flash remains selected with today's user-attested free gate.
Entrypoint verifies authenticated exact-model access, then uses the existing
six prepared requests/cache, unchanged packing/prompt/settings/retry limits.
Return terminal summary; inspect stop before retrying any quota/ambiguous call.
OpenAI remains blocked by unrevoked exposed key and unresolved fallback gates.


## Live-access resolution checkpoint — 2026-11-06 (latest; supersedes older access status)

Read `Agents.md` (actual case; `AGENTS.md` is absent), README and saved state.
Selected Gemini `gemini-2.5-flash` following the user's Gemini-first decision.
User confirmed eligible free quota in the owning project's console. Recorded
model/date-scoped operator attestation in ignored `.env`; no independent billing
verification claimed. New Gemini key moved from `.env.example` to `.env` without
printing; example credential fields empty, model setting nonsecret. Both keys
present locally; no exact secret matches in other scanned workspace files.
Git history remains unaudited. User says exposed OpenAI key is NOT revoked:
revocation is mandatory; no OpenAI fallback now, and no credits/model assumed.

Agent TCP/UDP socket creation fails with EPERM (1). Google/OpenAI/neutral DNS
fail with EAI_AGAIN (-3); HTTPS fails at DNS before any TLS handshake. No proxy
variables configured. Default trust loads 145 CA certificates; remote certificate
status untested. WSL2 kernel detected, ordinary terminal network unverified.
No restriction bypass, TLS disablement or repeated authenticated request.
Redacted checkpoint: artifacts/access_diagnostics/network.json and access_review.json.

Minimal setup fix: Gemini entrypoint now loads only its allowed literal `.env`
settings through the existing parser, with process overrides. Both integrations,
all frozen questions/settings/budgets/retries, packed-only boundary and ledgers
preserved. 23/23 tests pass, including isolated Gemini configuration; mock scores
remain mock checks. No live API metadata/count/generation requests this session.
No real prediction, measured provider usage/latency, or official live scores.
Cannot provide a real-prediction walkthrough before a live response exists.

Official Google documentation reviewed: API-key header, models.get, pricing,
limits and current Firebase availability notice. Gemini 2.5 is deprecated with
access restricted to previously active projects; current notices mention routing
changes December 1. Older indexed model/deprecation statements conflict, so
exact authenticated access/resolved model still requires verification. No model
substitution or extra provider authorized/performed; $0 policy retained.

One concrete next action: in ordinary WSL run
`cd /home/p_2626/BigDataEndSem/final` then
`/home/p_2626/bigdata-env/bin/python scripts/check_network_access.py` and return
its redacted JSON. Public, unauthenticated workers have ten-second bounds;
compare socket/DNS/verified HTTPS outcomes with agent evidence. If successful,
README gives the existing Gemini run command for that terminal. Complete only
the six fixed requests, checkpoint quota/uncertain completion, preserve cache,
score officially, explain one real prediction, update docs, then stop.



Last updated: 2026-11-06. Phase: **Gemini retained; OpenAI alternative tested offline; live smoke awaits OpenAI model and free-credit verification**. See the final dated milestone section for current verification and setup; earlier sections preserve history. No live model runs.

## Current decision

Research question: at fixed model and evidence budget, does preserving structural dependencies when packing evidence improve official answers and reduce wrong-operand errors?

Selected architecture: six prediction-safe readers → local Spark preparation/overlap audit → within-context lexical retrieval → dependency-preserving evidence packing → a quota-aware free-provider client producing a typed answer plan (model fixed within each controlled comparison block) → local validated execution/extraction → dataset output adapters and official evaluators. Shared extraction, arithmetic, comparison, hypothetical overlays and predicted conversation state; no dataset-selected models, no training in the main study.

Canonical documents:

- [discovery.md](discovery.md): verified repositories, counts, schemas, evaluator hazards, overlap, implementation audit, hardware and report requirements.
- [research.md](research.md): primary sources, closest work, falsifiable hypothesis, fair comparisons and report evidence map.
- [proposal.md](proposal.md): chosen architecture, component contracts, resource/cost estimates and operating policy.
- [plan.md](plan.md): small dependency-ordered tasks, checks, gates and first experiment.

## Completed in this planning pass

Read actual `Agents.md`, all initial docs and prior implementation materials before design. Inspected six repository origins/HEADs/readmes, available data schemas/counts (ZIP in memory), evaluator source, report template and visible environment. Read original papers and searched close work including TAT-LLM, PoT, EEDP, FINDER and FinCARDS. Audited preprocessing claims and identified leakage risks without alleging an unobserved leaked run. Performed preliminary exact overlap checks. Saved only planning documents inside final; no parent changes, installations, paid calls, model training, dataset extraction or implementation runs.

## Material blockers and uncertainties

1. **Data completeness:** MultiHiertt raw dataset absent; HybridQA linked table/passage corpus absent. Six repositories do not equal six runnable datasets. Source links identified; successful acquisition still unverified.
2. **Model/API:** user confirmed $0 spending and quota-driven switching across Gemini, OpenAI, OpenRouter, Groq and Mistral. Exact free models, credentials, account eligibility, limits/reset times and provider order remain unknown. No paid fallback; paired variants use the same provider/model. No useful local text model/runtime verified. GPU blocked in this session; CPU + API is the selected execution path, conditional on access.
3. **Deadline/rubric:** user confirmed **8 November 2026** and that Spark/Hadoop are optional. Submission time, page limits and demo requirements remain unknown. Prioritize the QA pilot and report; measure Spark without unnecessary HDFS setup. Full six-dataset runs within this deadline are not promised.
4. **Scoring:** TAT-QA original public test and test-gold have incompatible IDs/counts; choose the released test-gold version explicitly for local test evaluation. TAT-HQA CLI has undefined `qcnt`; plan a wrapper preserving metric logic. Other evaluator denominator and invalid-output quirks require tests before calls. Hidden-test scoring service availability unverified.
5. **Overlap:** measured 9 exact TAT-QA-dev question+table pairs in TAT-HQA factual train, with much same-split reuse; FinQA/ConvFinQA share sources. Complete persisted exact/near-duplicate audit is pending; no pooled training/demonstration bank until addressed.
6. **Resources:** measured ~47 GiB guest RAM/8 logical CPUs/~922 GiB virtual free disk. Physical host disk and claimed RTX 4060 VRAM not verified; package metadata does not establish runtime compatibility. `pdflatex` absent from PATH; final is not currently recognized as a Git repository.
7. **Research outcome:** all gains are hypotheses. Similar systems exist; contribution is the controlled packing mechanism/study, not a novel retrieve–reason–execute pipeline. No final accuracy, speedup or cost has been measured.

## Historical next action from planning (superseded by milestone below)

The planning pass originally said to remain in planning until implementation authorization. Then start T0/T1: freeze source/split manifests and implement a prediction-only FinQA reader with separate references. Complete ten training fixtures through restricted execution and official-format scoring before the first model call. The first research experiment is 20 fixed FinQA dev questions, B1 versus P, with matched model/budget and saved official predictions. Expand within the same package after that slice works.

Historical prototype preprocessing figures remain unverified; no result from it is accepted as reproduced. No test set has been used to tune this proposal.

Planning amendment: free-provider rotation is recorded in proposal.md, research.md and T3 in plan.md. No clients implemented or keys requested; no inference calls made. Budget is resolved ($0), while free capacity is not.


## Completed local milestone — 2026-11-06

Authorized scope: ten fixed FinQA training examples, no model/API calls,
installations, training, acquisition or unrelated repairs. The actual instruction
file `Agents.md` was read; `AGENTS.md` does not exist. Parent datasets and the old
implementation were read only. Saved proposal remains the design.

Implemented `src/nrqa/{core,finqa,execute,evaluation}.py`, the handwritten
`experiments/finqa_test_fixtures.json`, `scripts/run_local_finqa.py`, six semantic
unittest checks, and README reproduction/data-flow instructions. Outputs live
in `artifacts/local_finqa/`. Manifest records source revision, full train-file
hash/count, exact ten IDs, fixture hash, budgets and zero model calls; metrics
record the unchanged official scorer hash. The full train file is loaded, but
only its first ten fixed IDs are converted/evaluated in this milestone.

Reader whitelists document/question fields and separates ReferenceRecord.
Evidence preserves normalized/original tables, paragraph-local offsets, stable
cell coordinates, original strings, parsed decimals where unambiguous, unknown
scales and inferred-header uncertainty. Conservative unit-mention dependencies
retain their paragraph sources. Shared adjacency closure supports future header,
link and state dependencies without adding other readers now.

Ordinary lexical overlap ranking is deterministic. Ordinary packing includes
readable headers; proposed packing recursively includes required dependencies,
deduplicates them and admits only complete bundles within budget. Both log a
4,000 estimated-token cap. Counting is ceil(UTF-8 bytes/4) over serialized
facts including provenance; it is not a model-token guarantee. An injectable
counter interface allows replacement with the chosen tokenizer later.

Executor uses grounded spans, allowlisted constants, bounded Decimal arithmetic,
prior-step validation, extraction, failure records and operation traces. Supports
add/subtract/multiply/divide/greater/bounded integer exponent for this slice.
Unknown units are logged, not treated as semantic proof. Official FinQA export
covers these arithmetic plans; extraction is local only and never compiled into
a fabricated identity program. Test fixtures were handwritten with training
labels visible; repeated numeric selectors choose the first input occurrence.
They are engineering fixtures, not a reasoning algorithm or model prediction.
The runner never turns reference programs into predictions.

Checks actually run: `PYTHONPATH=src /home/p_2626/bigdata-env/bin/python -m unittest
discover -s tests -v` — **6/6 passed**. Includes all ten reference mutation/deletion
checks, source/header/unit preservation, recursive closure/deduplication/cycle and
too-small-budget checks, arithmetic/negative/percent/extraction tests, invalid
references/steps/operators/division/exponent tests, official rounding/percent/
invalid-division semantics, exact scorer ID coverage, and two complete repeated
runs with identical hashes for every JSON artifact. Existing NumPy, SymPy and
tqdm imports succeeded; nothing installed.

Official scorer outcome: **10/10 execution checks and 10/10 symbolic program
checks for handwritten training test fixtures**. These use all supplied evidence
under a separate explicit 100,000 estimated-token cap, not the 4,000-token
retrieval bundles. Thus no retrieval success, model accuracy, improvement, dev
score or full-dataset score follows from these numbers.

### Six-dataset evaluation coverage and remaining gates

| Dataset | Actual evaluation this milestone | Planned evaluation / unresolved gate |
|---|---|---|
| FinQA | 10 train handwritten fixtures only; unchanged official scorer | Later fixed dev comparison then frozen full available split; tokenizer/model gate; table aggregate/export coverage remains |
| ConvFinQA | 0 | Shared-core reader, predicted sequential state, cumulative official compiler and scorer adapter; ZIP available per discovery; hidden test needs external scoring |
| TAT-QA | 0 | Reader, scale/multi-span and evaluator adapter; use matching released test-gold inputs/IDs, never original-test position joins |
| HybridQA | 0 | Linked table/passage corpus missing per discovery; acquire and audit before reader/full dev EM/F1; hidden-test scoring availability unresolved |
| TAT-HQA | 0 | Hypothetical reader/overlay and adapter; bypass documented official CLI qcnt defect without changing metrics; hidden-test scoring unresolved |
| MultiHiertt | 0 | Raw data missing per discovery; acquisition/schema audit, HTML hierarchy reader and combined evaluator required |

Data/evaluator blockers above inherit the saved discovery audit, not a fresh
acquisition attempt. No dataset has been removed. Full six-dataset evaluation
remains planned, conditional on data/evaluator access and measured runtime.
Report exact split denominators, failures and missing datasets for every future
run; never call a sampled run full-dataset evaluation.

Next action requires a later milestone: extend validated operation/schema tests
and/or add the next reader under the same core, then freeze a tokenizer/model
and matched dev protocol before any model-backed comparison. API eligibility,
missing corpora, overlap auditing and evaluator compatibility remain unresolved.
**Stop here: the requested first local milestone is complete.**

## One-provider integration milestone — 2026-11-06 (historical; setup superseded below)

The latest user instruction authorizes one integration and a three-dev-question
two-packer smoke test. It supersedes the preceding local-milestone stop. Current
phase: **local API integration verified; real inference blocked by configuration**.
No new datasets, redesign, scheduler, paid call, installation or training.

Read `Agents.md` (actual filename; no `AGENTS.md` exists), proposal/plan/state and
all completed FinQA source/tests. Confirmed the old fixture runner intentionally
uses full context. New production path imports neither fixture plans nor its
full-context execution path. `model.request` whitelists only question and packed
fact ID/raw/unit; execution receives the same packed facts. Tests mutate gold
fields and the full document, and reject an operand absent from the pack.

Added `model.py`, `providers.py`, `runner.py`, `run_api_finqa.py`, an explicit
mock-smoke script, fixed dev configuration, environment example, ignore rules
and nine initial API tests plus one arithmetic integration test. Together with
the six original tests, **16/16 pass** in the existing bigdata environment.
No secrets were printed or copied into tracked-intended files. `api.txt` has
Gemini project details and an OpenAI-style credential; no recognizable Gemini
key was found. No GEMINI_/GOOGLE_/NRQA_ variables were configured. No Git commit
was created (usable Git metadata remains absent).

Implementation: Gemini REST JSON-schema output, strict local parsing and
existing executor, provider-independent protocol, exact-request SHA-256 keys,
SQLite atomic progress, raw-before-parse storage, durable attempt accounting,
file lock, bounded 5xx retries, immediate quota stop and conservative no-retry
handling for ambiguous transport. No semantic repair or label substitution.
Preflight binds the supplied key to its owning project using a read-authorized
OAuth credential, requires billingEnabled=false, verifies a reviewed free-tier
model and pins model metadata. Only `gemini-2.5-flash` is reviewed/enabled;
unknown models fail closed. No paid fallback/top-up or provider scheduling.

Live counting uses provider countTokens on exactly serialized evidence, with
memoized counts; input-text counts exclude system/schema overhead, with actual
whole-request usage separately retained from usageMetadata. Offline preparation
uses clearly marked estimates. Mock counts and usage are synthetic. Settings:
4,000 evidence tokens, temperature 0, top-p 1, candidate count 1, thinking 0,
2,048 output tokens, 60-second HTTP timeout, three attempts/request maximum,
18 total generation attempts, 1,000 token-count requests/invocation maximum.

Saved verification: `artifacts/api_mock_finqa/` contains all six mock requests,
selected/packed evidence, raw abstentions, parsed output, execution statuses,
latencies, synthetic usage, official prediction files and metrics. Official
scorer SHA-256 remains
`845cd131cab843eceff256cf6d392978cc470a7da4a80107beb56027fdca5c13`.
Each mock variant has denominator 3 and 0/3 execution, 0/3 program checks,
expected from forced abstention. **These are not model accuracy results.**
The first mock invocation dispatched six requests; immediate resume reused all
six and dispatched zero. `mock_verification.json` records the proof. A separate
synthetic 10/100 test traverses provider→ledger→execution→official eval and
returns 0.1 without references.

Real invocation: `artifacts/api_finqa/manifest.json` records
`blocked_before_inference`, zero model calls, no official scores, and missing
`GEMINI_API_KEY`, `GEMINI_MODEL`, `GOOGLE_PROJECT_NUMBER`, `GEMINI_KEY_ID`,
`GOOGLE_OAUTH_ACCESS_TOKEN`. Six estimated preparation bundles are saved;
these will be repacked with countTokens for live inference. IDs fixed before
calls: `V/2008/page_17.pdf-1`, `C/2017/page_328.pdf-1`,
`DVN/2007/page_58.pdf-2`. No live model output, measured provider tokens/latency,
account quota availability or architectural improvement is claimed.

Next action, once local setup is supplied: follow README's five-variable setup
for a billing-disabled owning project, run the API script and rerun it to check
real cache reuse. Account regional eligibility, free quota and hosted model
availability remain unverified. Gate failure or quota exhaustion must save and
stop. Timed-out/inflight requests require inspection because remote completion
is uncertain. Policy review is dated 2026-11-06; provider aliases are not a
promise of immutable hosted weights. Exact requested/metadata/resolved models
are recorded and observed drift stops scoring. The three-question sample is a
smoke test only; all broader study and six-dataset coverage gates remain pending.

Stop after reporting this milestone. No larger study or extra integrations are
authorized by the current instruction.


## Authentication review and live smoke gate — 2026-11-06 (current)

Read actual `Agents.md` (`AGENTS.md` is absent), README, state, plan, and the
Gemini integration, runner, request boundary and tests. User authorizes the
existing three-question live comparison only after free-only eligibility is
established, then reporting and stopping. No broader study or tuning authorized.

Confirmed endpoint: Gemini **Developer API**, not Vertex AI, at
`generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash`.
Official Google REST authentication requires an API key in `x-goog-api-key`.
Only `GEMINI_API_KEY` is required for authentication; `GEMINI_MODEL` now defaults
to the same frozen 2.5 Flash. Removed mandatory project number, key ID and OAuth
configuration and the administrative key-string/billing calls. Those credentials
served optional ownership/billing audits, not inference or remaining-quota proof.
README links Google's authentication, models, pricing, billing, limits and admin
API references. Official search extracts were accessible; full-page opens failed
with markdown/redirect errors. Public standard 2.5 Flash free pricing is documented,
but this account's availability and eligibility remain **unverified**.

Free-use gate now requires operator console confirmation, scoped to this model
and the current UTC day: `GEMINI_FREE_TIER_CONFIRMED=gemini-2.5-flash:YYYY-MM-DD`.
Before setting it, inspect the configured key's owning project in AI Studio:
Free tier, Cloud Billing disabled/unlinked, and nonzero model RPM/TPM/RPD plus
usage headroom. No billing enablement or model substitution. This is expressly
an operator attestation, not an independent account verification or a Google
authentication credential; it must be renewed when keys/projects change.
Authenticated models.get subsequently checks exact model/version and both
required methods. Unknown model, absent/stale/wrong-model confirmation, missing
key or unavailable metadata fails closed. No paid fallback or resource creation.
The console gate relies on accurate confirmation and does not remotely monitor
subsequent billing changes. This replaces the historical five-variable setup.

Current process has no Gemini API key or console confirmation. The real smoke
entrypoint was invoked and saved `blocked_before_inference`,
`missing_configuration:GEMINI_API_KEY`, **zero generation/countTokens/metadata
calls**, and no live scores. `artifacts/api_finqa/access_review.json` records
both blockers; `manifest.json` and six estimated preparations remain separate
from mock artifacts. No completed live request or ledger was removed. The
three IDs, two packers, prompt/schema, evidence cap, generation and retry
settings are unchanged. No reference fields are added to inference inputs.

Credential audit: inspected `api.txt` only in local memory, without printing,
prompting or persisting its contents. No recognizable Google key pattern;
an OpenAI-style secret is present. No exact detected credential string matches
in other workspace files, including artifacts. Ignore rule exists. `.git` is
empty, and `git ls-files` fails; tracking/history cannot be established. No
observed exposure in checked files; no claim that the secret was never committed
or exposed elsewhere. No credentials in the saved review.

Validation: **17/17 tests pass** in the existing environment. Includes minimum
key-only authentication configuration, unavailable model/missing methods,
missing/stale/mismatched console confirmation, reference isolation, official
execution, cache reuse, retries and quota checkpointing. The temporary mock
three-question run resumes all six completed requests without new generation.
No new mock accuracy claim; no packages installed.

No live prediction exists to explain through execution/scoring or classify as
retrieval, missing context, reasoning, output format, execution or evaluation
failure. This is an access blocker before those stages. No method tuning or
improvement claim. Proposed method fixes: none based on nonexistent live results.

Exact next action: supply the Gemini key locally, complete the two README console
checks and set the dated confirmation. Then resume `scripts/run_api_finqa.py`
with the existing output directory/ledger; repeat to verify cached completion.
If any 402/429 occurs, checkpoint and stop. After completion, explain one real
prediction and classify observed failures, with proposed fixes kept separate.
**Stop now: exact remaining access blocker reported.**


## Explicit OpenAI alternative — current status

The user requested OpenAI now and Gemini later. Preserved the Gemini adapter,
entrypoint and artifacts. Added `openai_provider.py` and `run_openai_finqa.py`,
which reuse the same fixed three dev questions, both packers, instructions,
local validation, executor, official scoring and durable ledger. OpenAI has its
own `artifacts/api_openai_finqa/` directory and explicit model selection.
No automatic model/provider fallback or spending-policy relaxation.

The user identified `final/.env`. The key was actually found in `.env.example`
during the initial read and exposed in tool output. It was moved locally to
ignored `.env` with mode 0600; the example now has blank values. Recommend
rotation. The same key also remains in pre-existing ignored `api.txt`; no exact
credential matches in other checked source/artifact files after relocation. This supersedes earlier no-observed-exposure reports for this key;
Git tracking/history remains unknown. No credential contents in the review file.

The OpenAI route parses only whitelisted .env assignments as literal strings,
without shell execution; process env overrides them. Authentication requires
`OPENAI_API_KEY`; legacy `OPEN_AI` is accepted. `OPENAI_MODEL` is explicit,
without a default or automatic replacement. The current .env has only the key.
Before any provider call, require model/date-scoped
`OPENAI_FREE_CREDITS_CONFIRMED=MODEL:YYYY-MM-DD`: operator confirms sufficient
unexpired free API credits, no paid payment method/recharge and model quota.
The path-only user reply did not confirm credits. models.get later establishes
model access, not credit status. No inference until the free-only gate passes.
Official OpenAI documentation links and console checks are in README.

OpenAI uses Responses JSON mode plus unchanged local schema validation. Fixed
settings for both variants: temperature 0, top-p 1, one response, 2,048 output
tokens; Gemini's thinkingBudget is omitted. No paid or unsupported-setting fallback.
Evidence counts use responses/input_tokens on evidence-only input including
framing; actual usage and resolved model are retained from raw response fields.
Three attempts/request, 18 total; existing cache and quota stop retained.

Validation: **22/22 tests pass**. New OpenAI mock checks cover literal env loading,
free-use gate, authentication, packed-only request, actual-shaped usage records,
refusal/incomplete outputs, quota restart stop and the paired smoke with 6 cache
hits/zero new generation calls on resume. Mock abstentions and usage are synthetic,
with artifacts only in test temporary directories. Existing Gemini checks pass.

Real OpenAI entrypoint: `blocked_before_inference`, missing `OPENAI_MODEL`;
**zero authenticated metadata/count/generation calls and no live scores**.
`access_review.json` also records unverified free-credit status. No live prediction
exists to explain or classify; no answer-based tuning or improvement claim.

Remaining blocker: choose/configure the OpenAI model and confirm the key-owning
organization's free credits/no paid billing/model quota using README's console
checks. Then resume the OpenAI entrypoint, preserve cache and stop on quota errors.
Report real outcomes and one prediction walkthrough only after live completion.


Subsequent read-only authentication check: attempted GET /v1/models once using
the .env key in an Authorization header, without printing credentials or saving
remote error bodies. Connection failed with ambiguous_transport before any
model-list response. Key validity remains unverified. access_probe.json records
latency and error. The smoke itself still dispatched zero provider calls;
aggregate activity is one metadata attempt, zero successful metadata responses,
zero count/generation requests. Network connectivity is another live-access
blocker; no paid operation was attempted.
