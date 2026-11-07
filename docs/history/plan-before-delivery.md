# Actionable implementation and experiment plan

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



Status: local FinQA slice and one-provider integration implemented, 2026-11-06; live smoke blocked by missing Gemini key and unverified account eligibility; latest authentication amendment supersedes historical five-variable setup. The original task table below remains the broader plan; dated milestone amendments record actual completion. All new work stays inside `final/`; parent sources remain unchanged.

## Scope and gates

One package, six readers/evaluators, one evidence/reasoning workflow. First deliver a small FinQA vertical slice, then extend input and answer capabilities. Do not build six separate systems or finish all infrastructure before a question can pass through the core.

Main study uses frozen models within matched comparison blocks, without fine-tuning, and a quota-aware pool of free providers. Spending ceiling is $0; exact models, credentials and account quotas are pending. Dataset acquisition is required for HybridQA and MultiHiertt; do not manufacture substitute records for performance reporting. Synthetic fixtures can test schema/executor behavior only. Final test labels stay outside the inference process and development decisions.

Confirmed deadline: **8 November 2026**, time unspecified. Spark/Hadoop are optional; prioritize QA/evaluation and measure Spark on preparation/overlap work without deploying HDFS. The brief's “tomorrow” wording is superseded.

Dependency chain: T0 → T1 → T2 → T3 → T4 → T5. T6–T9 extend the same slice after T3/T4; T10 requires all available readers; T11 requires evaluated baseline/pilot; T12 requires frozen configuration. T13/report evidence collection starts with T0 and completes after measured runs.

## Tasks

| Task / one goal | Included / excluded | Likely files inside final | Dependencies | Acceptance criteria and relevant checks |
|---|---|---|---|---|
| T0. Freeze input and run contracts | Include source paths/HEADs/checksums, expected counts, split identities, reference firewall and run schema. Exclude data transformation/model calls. | `configs/datasets.yaml`, `src/nrqa/contracts.py`, `artifacts/manifests/`, `tests/test_contracts.py` | Planning complete; no unresolved requirement needed for local contract work | Every available split named and counted; unavailable files explicit. Test-gold is its own TAT release. Model input type has no answer/program labels. Missing/extra IDs are errors. |
| T1. Read one FinQA example safely | Include FinQA train/dev reader, original tables/text, source IDs and separate labels. Exclude other readers and retrieval optimization. | `src/nrqa/readers/finqa.py`, `src/nrqa/evidence.py`, `tests/fixtures/`, `tests/test_readers.py` | T0 | Ten training fixtures preserve source strings/coordinates; deleting or replacing gold fields leaves inference JSON identical. Full reader counts match manifest or explicit error list. |
| T2. Complete deterministic reasoning and scoring path | Include restricted operation interpreter, trace, FinQA program-token compiler, evaluator wrapper and handcrafted plans. Exclude LLM calls and prompt tuning. | `src/nrqa/reasoning/{plan,execute}.py`, `src/nrqa/evaluation/finqa.py`, `tests/test_execute.py`, `tests/test_evaluation.py` | T1 | One train fixture passes reader→plan→execution→official output→score; invalid references, zero division, percent/sign/rounding and missing predictions tested. Handcrafted outputs clearly labeled test fixtures. Symbolic program scoring retained. |
| T3. Make one shared model-backed baseline | Include ordinary lexical evidence packing, common prompt, model client interface, cache/ledger and B1. A stub transport tests replay first. Exclude dependency expansion, repair loops and training. | `src/nrqa/retrieval.py`, `src/nrqa/model.py`, `src/nrqa/run.py`, `prompts/answer_plan.txt`, `configs/pilot.yaml`, `tests/test_resume.py` | T2; real calls additionally need API access, exact model and explicit cost ceiling | Ten fixture requests produce valid or explicitly failed records. Interrupted/restarted run reuses completed calls. Credentials absent from artifacts. First real calls restricted to agreed pilot; record latency/tokens/cost. |
| T4. Add the proposed packer | Include dependency edges, greedy closure, deduplication, strict token cap and logging. Exclude neural retrievers/graph databases/rerank agents. | `src/nrqa/packing.py`, `tests/test_packing.py`, `configs/variants.yaml` | T3 | Same candidates/model/executor support B1 and P. Every selected cell retains required header/unit sources; no token overflow. Fixtures cover a budget too small for closure, duplicate values and merged headers. |
| T5. Run first falsifiable pilot | Include 20 fixed FinQA dev questions, B1 versus P, paired official scores and manual error review. Exclude test and statistical superiority claims. | `experiments/pilot_ids.json`, `runs/<pilot>/{manifest,predictions,traces,metrics}.*`, `analysis/pilot.md` | T4 + API gate | 40 initial requests max, retry ceiling recorded; exact denominators and actual tokens reported. Identify whether differences arise from evidence, arithmetic or format. If no benefit, record that and inspect mechanism before expansion. |
| T6. Add TAT-QA and TAT-HQA semantics | Include two readers, span/multi-span/count/scale, temporary hypothetical overlays and separate reference records. Exclude gold intervention inputs and related-answer shortcuts. | `src/nrqa/readers/{tatqa,tathqa}.py`, `src/nrqa/evaluation/{tatqa,tathqa}.py`, executor extensions, relevant tests | T2/T4 | Ten train fixtures each, including zero, percent vs percentage points and intervention scope. TAT-HQA wrapper bypasses CLI typo without changing metric semantics. Correct release IDs; raw input fields yield processed-label scoring without leakage. |
| T7. Add sequential conversation support | Include ConvFinQA ZIP reader, questions-only prefix, prediction state, cumulative program export and resume by conversation. Exclude original source questions, future turns and gold prior answers. | `src/nrqa/readers/convfinqa.py`, `src/nrqa/history.py`, `src/nrqa/evaluation/convfinqa.py`, `tests/test_history.py` | T2/T3 | Three complete training conversations run through core. Altering future turns/gold prior answers cannot change current prediction inputs. Private-turn schema fixture retains prefix. Trusted scoring attaches reference programs only after inference. |
| T8. Restore and support HybridQA input | Include obtaining official linked corpus into final/data, version/hash record, ID mapping, link-aware reader and output adapter. Exclude use of traced answer nodes as evidence and broad Wikipedia crawl. | `data/raw/WikiTables-WithLinks/`, `src/nrqa/readers/hybridqa.py`, `src/nrqa/evaluation/hybridqa.py` | T0/T4; external data access | Corpus completeness audit resolves every table/link or produces explicit missing list. Ten train examples include at least one linked-text hop. Official overall/subgroup EM/F1 and denominators correct. If unavailable, dataset remains blocked in results. |
| T9. Restore and support MultiHiertt input | Include official raw data acquisition, actual schema/count audit, HTML cell/span parsing, hierarchy and span/program export. Exclude trusting gold-prepared reasoning inputs or training MT2Net. | `data/raw/MultiHiertt/`, `src/nrqa/readers/multihiertt.py`, `src/nrqa/evaluation/multihiertt.py`, parser fixtures | T0/T4; external data access | Verify actual splits/hashes first; ten train examples preserve original cell IDs and header ancestry. Both span and program outputs score through official logic; invalid programs fail safely. No six-dataset completion claim without data. |
| T10. Prepare corpus with measured Spark work | Include batch parsing/joins/fingerprints/Parquet, cross-split overlap matrices and Python equivalence. Exclude API calls in workers, HDFS daemon deployment and synthetic QA counts. | `src/nrqa/data_jobs.py`, `src/nrqa/overlap.py`, `artifacts/data_audit/`, `benchmarks/prepare.py` | T1/T6/T7/T8/T9 for full six-way run; available subsets can run earlier | Counts plus failures equal raw manifest. Python/Spark canonical hashes match. Recover known TAT overlap; inspect fuzzy matches. Save cold/warm wall time, RAM, spill and data-size results. Record Spark slowdown if present. |
| T11. Run paired multi-dataset development study | Include fixed sampled dev IDs, B0/B1/P/A2, official scores, traces and grouped errors. Exclude test-driven tuning and claiming published baselines reproduced. | `experiments/dev_protocol.yaml`, `runs/`, `analysis/{compare,errors,resources}.py`, `artifacts/tables/` | Relevant readers/evaluators, T5 and T10; remaining API budget | Target 100 questions/dataset, whole conversations for ConvFinQA (record actual turns). Same cap/model/call policy; predeclare samples and paired CIs. Blocked datasets and uncertainty visible. Expand only after measured cost/time check. |
| T12. Freeze and evaluate final inputs | Include final config/source/prompt/model hashes and one locked run; independent scoring. Exclude changing design after seeing test outcomes. | `experiments/final_protocol.yaml`, `runs/final/`, `artifacts/tables/final.*` | T11; test access and available time | FinQA public and correct TAT test-gold input versions used. Hidden tests get valid export only unless official scoring is obtainable. Held-out dev remains labeled as such. Save all failures; separate official QA and optional corpus-retrieval tables. |
| T13. Assemble defensible report | Include format copy, real result tables, method diagram, related work, limitations, reproduction commands and appendix traces. Exclude unsupported targets, invented speedups and template-example claims. | `report/main.tex`, `report/references.bib`, `report/figures/`, `artifacts/report_evidence.csv`, `docs/state.md` | Starts T0; finishes after whatever measured runs actually complete | Every number maps to artifact + evaluator/run ID or cited publication. Compile local copy with proper style case; check references, figures and unknown course requirements. No editing upstream template. |

## First experiment and expansion schedule

The first end-to-end engineering slice uses ten FinQA training fixtures and handcrafted plans before model access. Its purpose is to prove input isolation, execution and official scoring; it is not a model result. The first research experiment is T5: a seed-fixed 20-question FinQA development sample, comparing B1 and P with one model, one call each and a 4,000-token evidence cap. Select by stable ID sampling, not by whether the proposed method is likely to win. Log evidence availability, operand mistakes, execution/program accuracy, token counts, latency and billed cost. A separate labeled diagnostic can inspect ambiguous-year cases; do not confuse it with the random sample.

After that, ten training fixtures per added reader establish capability coverage. The multi-dataset development study targets ~600 questions (whole conversations alter the exact total). At four variants this is ~2,400 first attempts, not a trivial free run. Scope is reduced by number of questions/ablations if the cost/time gate fails, while retaining shared architecture and honest dataset coverage. Full development and locked tests are conditional later steps.

Indicative effort estimates, not commitments: T0–T2 2–4 focused hours; T3–T5 2–4 hours plus API availability; additional readers/capabilities 4–10 hours; acquisition/evaluator compatibility 1–4 hours with substantial uncertainty; Spark audit 1–3 hours; report 2–4 hours; model runs add elapsed time from proposal.md. This is 12–29 focused work hours before substantial model runs and uncertainty. Prioritize a working vertical slice, a measured paired pilot, transparent six-dataset support status and a report of evidence actually obtained. Do not promise six complete benchmark reproductions by 8 November.

Provisional deadline checkpoints: 6 November—contracts and first vertical slice; 7 November—extend readers, resolve corpus/evaluator gates, run paired development study and freeze design; 8 November—finish any locked evaluation and report. Reserve at least four hours for report assembly/compilation and stop expanding scope then. This is a proposed implementation schedule, not work authorized or performed during this planning turn. Missing API/data access reduces measured scope, not reporting honesty.

## Validation and artifact rules

- Build a small semantic test suite for numerical parsing, evidence identity, hierarchy/links, temporal isolation, output formats, evaluator edge cases and resumability. These are consequential correctness checks, not tests that merely mirror implementation.
- Use a standard-library test runner if desired; missing pytest is not a reason to install during planning. Pin dependencies during the later implementation phase after checking compatibility.
- Keep reference data in an evaluation-only store; the inference API accepts only the prediction schema. Reference-field mutation tests are mandatory before the first API call.
- Batch local preparation by file/partition; write per-example model results immediately and checkpoint each conversation turn. Never rerun successful API requests merely to recompute metrics or tables.
- Record source revisions, model revision, prompt text/hash, cap, sample IDs, seed, history protocol, attempts, tokens and spend for every variant.
- Official baselines remain cited published rows unless their actual checkpoints and outputs are reproduced. The existing implementation is not an accuracy baseline.
- Follow the report-evidence map in research.md; update state.md at each meaningful milestone, with current blockers and the next concrete action.

Next concrete action after planning authorization ends: T0 and T1, using available FinQA data; in parallel resolve corpus access and the submission time and free API eligibility/quotas. No need to wait for those answers to define or test local input contracts.


## T3 amendment: free-provider client and matched-block scheduler

Included: provider registry, zero-spend allowlist, cooldown/reset handling, per-provider token/request counters, resolved model logging, model-specific caches and paired-block queue. Likely additional files: `configs/providers.yaml`, `src/nrqa/providers.py`, `src/nrqa/scheduler.py`, `tests/test_quotas.py`. Excluded: paid fallback, automatic top-ups, model selection based on answer quality, and training. Dependencies: T2 plus verified free-access settings before real calls. Acceptance checks using mocked transports: 429 cools one provider and dispatches eligible fresh work elsewhere; daily exhaustion waits for reset; all-exhausted state checkpoints without a call; maximum three attempts total; mismatched-model pairs cannot enter controlled scores; conversation state remains variant-specific; unverified or potentially billable routes are refused. Preserve incomplete-block counts and cached completed outputs across restart.

Before T5/T11, calculate paired sample capacity from actual free request/token allowances. Prefer completing a small fixed-model comparison to accumulating unmatched predictions. Provider pool candidates are Gemini, OpenAI (only verified free/credit-backed access), OpenRouter, Groq and Mistral; no priority or exact model is fixed yet.


## Local milestone status — 2026-11-06

The user authorized a focused offline slice, including retrieval and both
packers earlier than the original T3/T4 dependency schedule. Completed T1 and
the small T2 arithmetic path on ten fixed train IDs, plus local-only portions
of T0/T3/T4. Do not mark the broader tasks complete: full split manifests,
all official operation forms, provider client/cache, model runs, linked/conversation
readers and study remain pending. Source hashes and exact fixture coverage are
saved in `artifacts/local_finqa/manifest.json`; scorer checks and six passing
semantic tests are detailed in state.md. Token budgets remain estimates.

The ten handwritten test fixtures pass official execution and program checks
(10 each); these are not model results. Execution fixtures use complete context
with a separate 100,000 estimated-token cap. The two retrieval variants use
4,000 estimated tokens; no retrieval or accuracy benefit was evaluated.

Retain evaluation on **all six** datasets. Before T11, maintain explicit per-split
expected/attempted/scored/failure counts and blockers. FinQA has only ten train
contract fixtures evaluated now; the other five have zero. HybridQA corpus and
MultiHiertt data remain missing; TAT-HQA CLI and TAT-QA release identity need
adapters; ConvFinQA needs sequential predicted state and official export. Full
available development/test evaluation is still the target after adapters and
frozen configuration. If infeasible, publish actual sampled coverage and each
blocked dataset rather than silently reducing the dataset scope.

This turn stops after the first local milestone. No T5 experiment, model call,
package installation, training or unrelated dataset repair is authorized here.

## Authorized API smoke milestone — 2026-11-06

This amendment supersedes the earlier stop instruction and the multi-provider
T3 scheduling proposal **for this milestone only**. No architecture redesign,
other dataset integration, provider rotation or larger pilot is included.

Completed locally: provider-independent model protocol; one Gemini adapter;
environment-only secrets; fail-closed billing/key-project/model checks; structured
plans grounded exclusively in packed evidence; persistent cache/attempt ledger;
bounded retries and quota stop; provider countTokens adapter; saved mock run and
resumption proof. T3 is implemented locally, with real account access blocked.
The existing T4 packers are reused. T5's 20-question study remains pending.

Frozen smoke: `experiments/finqa_api_smoke.json`, first three dev records,
ordinary/dependency variants, 4,000 live evidence tokens, fixed Gemini
`gemini-2.5-flash`, identical schema/instructions/settings, 6 logical requests,
maximum 18 generation attempts. Provider metadata version and server-resolved
model are retained; mixed resolved versions cannot enter paired scoring.

Acceptance evidence: 16 semantic tests; six mock abstention records, official
0/3 execution and program checks per variant; resumed 6/6 cache hits and zero
new generation calls. Mock scores/usage/counts/latency are engineering fixtures,
never real-model results. A separate synthetic arithmetic plan passes the
mock-provider→ledger→validated executor→official arithmetic path.

Live gate outcome: zero inference calls, missing all five required environment
variables; no verified free account/model access. Complete the exact README
setup locally (Gemini key, owning numeric project and key ID, billing disabled,
read-authorized OAuth token, fixed model), then run `scripts/run_api_finqa.py`
twice. Preserve the ledger and inspect saved quota/ambiguous stops rather than
retrying blindly. Report actual six-request results and limitations, then stop.
No superiority claim can follow from this sample. All wider tasks remain pending.


## Authentication review amendment — 2026-11-06 (current)

Supersedes the administrative five-variable setup above. Gemini Developer API
inference uses only `GEMINI_API_KEY`; the frozen model defaults to
`gemini-2.5-flash`. Project number, key ID and OAuth token were needed only for
previous optional key-resource/billing audits. These calls/configuration were
removed; they did not establish model quota. Official sources and operation-specific
permissions are in README and `artifacts/api_finqa/access_review.json`.

Completed: fail-closed dated console-attestation gate, authenticated model metadata
check, minimum environment example, credential exposure check, 17 passing tests,
and live entrypoint checkpoint with zero inference calls. Account eligibility
and model availability on this account remain unverified. No live result,
latency, token usage, official score or prediction failure analysis exists.

Remaining access work, without enabling billing or changing models:

1. Configure a Gemini Developer API key locally. Do not load or publish `api.txt`.
2. For that key's owning project, confirm Free tier and billing disabled/unlinked;
   inspect AI Studio rate limits for 2.5 Flash, nonzero limits and usage headroom.
3. Only after those checks, set `GEMINI_FREE_TIER_CONFIRMED` to
   `gemini-2.5-flash:YYYY-MM-DD` for today's UTC date. This records operator
   attestation, not independent account verification. It is not authentication.
4. Resume the same smoke runner/output directory. Metadata checks must pass;
   preserve completed cached requests and stop/checkpoint on quota exhaustion.
5. Inspect six real outcomes with identical existing settings, explain one from
   packed evidence through execution and official scoring, and classify failures
   as retrieval, missing context, reasoning, output format, execution or evaluation.
   Keep proposed fixes separate. Do not tune on the three answers or claim a gain.

Current stopping point: missing key plus unverified free account/model quota.
No additional experiment is authorized while this blocker remains.


## User-authorized OpenAI alternative (current)

Keep Gemini for a later key; use a separate explicit OpenAI entrypoint/output
folder. Implemented safe literal .env loading, Responses JSON mode, local schema
validation, provider token counting, usage/model logging, shared cache/quota stops
and 22 passing tests. Both packers retain matched questions, evidence cap,
instructions, settings and retries. No provider rotation or paid fallback.

Live OpenAI smoke remains blocked by missing OPENAI_MODEL and unconfirmed
free-credit eligibility. Check the key-owning organization's Billing for
sufficient unexpired free credits and no paid payment method/recharge, and Limits
for model quota. Record current-date/model-specific operator confirmation in
OPENAI_FREE_CREDITS_CONFIRMED; this is not independent account verification.
Do not spend money, buy credits or select a replacement model automatically.

Key was misplaced in .env.example and exposed in tool output. Relocated to
ignored .env (0600), example cleared; rotation recommended. History cannot be
audited. Do not include either secret file in prompts/logs/artifacts.

Next: obtain model and eligibility configuration, resume the six logical live
requests in artifacts/api_openai_finqa, reuse cache, checkpoint quota stops, then
inspect real execution/scoring and report without tuning or a superiority claim.
Current exact blocker is recorded in that directory's access_review.json.

A separate read-only GET /v1/models authentication probe failed to connect
(ambiguous_transport). Resolve network access as well as model/credit configuration
before resuming; do not interpret this transport error as an invalid-key response.
No live inference was dispatched.
