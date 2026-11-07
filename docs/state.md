# Current project state — preserved live v4 audit

Updated 2026-11-06. **Live inference remains stopped and uncertain. Do not rerun
`artifacts/live_smoke_v4`, clear its inflight/uncertain state, or copy its ledger
into a new run.** No provider APIs, generation, credential files, or broad network
checks were used for this investigation. Public provider documentation was searched.
Local generation below means synthetic mocks only.

## What the failed run actually counted

Read-only SQLite inspection finds one logical request with two generation attempts:

- Dataset ID `V/2008/page_17.pdf-1`, variant `ordinary`; question: “what is the
  average payment volume per transaction for american express?”
- Logical request/cache key:
  `f9006fe1dcd32abfefc8f7a5485f985d63e8ae198ad9877b1c62d98fb21334b0`.
- Provider `gemini`, model `gemini-3.8-flash`, metadata version `3.0`.
  No successful generation resolved a model version.
- Both attempts target POST `/v1beta/models/gemini-3.8-flash:generateContent`.
  Attempt 2's path follows the saved request and provider code; its own old
  diagnostic object is empty.

| Attempt | Started UTC | Elapsed | Evidence and failure phase |
| --- | --- | --- | --- |
| 1 | 2026-11-06 20:37:29.405 | 2.898452 s | HTTP 503, `UNAVAILABLE`, provider message reports high demand. Dispatched and received an error response; failure belongs to the response phase, not a pre-dispatch/connection failure. Internal provider execution/completion unknown. |
| 2 | 2026-11-06 20:37:34.800 | 60.181521 s | `ambiguous_transport`; exception, timeout category and precise phase **unknown**. Duration is consistent with the 60 s socket timeout, but does not prove a response-wait timeout. Dispatch and remote completion unknown. |

`model_calls: 2` sums persisted generation attempt records, not successful outputs,
metadata checks, or token-count calls. There are 91 token-count cache rows and the
manifest reports 91 count calls; these are separate from the two generations.
Zero logical requests completed. No second dataset question or variant reached
generation in the available ledger.

## Saved responses, missing diagnostics, and retry risk

There is no `raw_response`, `response_saved` or completed request in SQLite, and no
`results.json` or separate response artifact in the directory. `current_input.json`
is a pre-dispatch input checkpoint, not a generated response. The only saved HTTP
body information is the first attempt's redacted 503 error. There is **no evidence
of a response saved locally but not committed to the ledger**. A partial/in-memory
response, discarded body, or remotely completed response cannot be excluded.
The runner saves successful raw output to `response_saved` before local parsing;
that checkpoint was never reached in the available record.

Two independent losses explain the empty terminal `error_details`:

1. The old transport catches URLError/TimeoutError/socket.timeout/OSError without
   binding the exception and raises `ProviderError('ambiguous_transport')` with
   default `{}`. Attempt 2 and the request therefore contain `{}`.
2. Ledger raises plain `StopRun(error.code)`, discarding details. The experiment
   wrapper reads `getattr(error, 'details', {})`, so even nonempty underlying
   diagnostics could disappear from the manifest. Attempt 1's 503 diagnostics
   remain only in its attempt record.

Automatic retry **did repeat this logical request** after the 503: the starts are
5.395 s apart, consisting of about 2.898 s call time and 2.497 s backoff. The code
permits up to three attempts after `transient_server` (HTTP 5xx), with bounded
exponential backoff and jitter when Retry-After <=60 s. It never automatically
retries ambiguous transport/response failures and resumption blocks uncertain or
inflight records. Those protections and the existing 5xx retry policy remain.
A received 503 does not itself prove zero remote execution or deduplication;
duplicate remote work from that retry cannot be ruled out. No third attempt was
recorded after the ambiguous failure. Neither attempt is relabeled safe to retry.

[Official generateContent reference](https://ai.google.dev/api/generate-content?hl=en)
and [Google's 429/503 guidance](https://discuss.ai.google.dev/t/handling-429-503-errors-from-the-gemini-api/124640)
were checked. The reference documents synchronous generateContent input/output and
an output `responseId`; no idempotency key, deduplication guarantee, or retrieval
of a lost synchronous response was found for this route. Google's recommendation
to back off after 503 is not an exactly-once guarantee. This is a documentation
finding, not a claim that all Google products lack recovery features. No recovery
endpoint or idempotency header was invented or called.

Earlier redacted diagnostics show ordinary WSL DNS and verified HTTPS succeeded,
while the agent environment had socket EPERM/DNS failures. They predate this run;
they cannot identify attempt 2's cause. The run's saved 503 establishes HTTP access
for attempt 1. Do not attribute the later failure to the old agent sandbox evidence.

## Correction and preserved experiment contracts

Transport errors now retain operation, endpoint path without query parameters,
exception/reason types, safe message, timeout category and monotonic elapsed time.
Known HTTP status and request-ID headers survive HTTP errors, body-read failures,
and decode failures. Stages distinguish pre-dispatch setup, urllib's combined
connection/send/header wait (**unknown substage**), response-body read, and decode.
Known credentials, authorization values, query values and full URLs are redacted;
headers, request bodies and raw error bodies are never logged. Dispatch outcome
remains unknown after opening begins. Diagnostic detail does not authorize retry.

Generation attempts and their error details carry a one-based attempt number and
logical request hash; token-count failures carry their count-request hash and
attempt number. `StopRun` retains details, including when an uncertain checkpoint
is revisited. The experiment wrapper can now preserve them in its manifest, including terminal HTTP failures returned as failed predictions.

All 21 `experiments/frozen_v4/` contracts, `contracts_v4.json`, and every live-v4
artifact retain their original bytes. Hash baselines and a read-only ledger audit
are in `artifacts/transport_diagnostics_v5/`. New source hashes require new
contracts: `experiments/frozen_v5/` and `experiments/contracts_v5.json` are created.
Only `code_hashes` and derived `contract` change; configs, IDs, inputs, settings,
prompts, schemas and source hashes match v4 exactly. Delivery checks use the new
registry, whose historical section includes all v4 contracts. The unchanged hash
guard intentionally rejects inference with v4 contracts under the corrected code.
No bypass, ledger conversion, cache deletion or live v5 run was performed. A future
new contract does not resolve or authorize replay of the uncertain v4 request.

Local/mock validation evidence is in `artifacts/transport_diagnostics_v5/`:
transport stage/redaction tests, ledger/manifest propagation, 503 followed by an
uncertain failure and blocked resume, existing retry ceilings, raw-response
recovery, and experiment contract/cache checks. See the saved test outputs and
`preservation_check.json`; all original hashes were compared again after checks.
33 tests passed (8 diagnostic, 13 API mock, 6 OpenAI mock, 6 experiment checks). All 21 final v5 code/contract hashes and 60 historical contract hashes passed local verification. Delivery contract/input checks also passed; no new full data-readiness validation was run. These are diagnostic checks, not measured model results.

## Safest next ordinary-WSL command

From `/home/p_2626/BigDataEndSem/final`, run this **offline, read-only** command:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/p_2626/bigdata-env/bin/python scripts/inspect_smoke_ledger.py artifacts/live_smoke_v4
```

It does not load `.env`, invoke a provider, instantiate a writable Ledger, or repair
anything. It prints attempt metadata and artifact hashes, excluding requests and
response contents. Do not run the broad network script or restart inference to
collect better diagnostics for this historical attempt; its lost exception cannot
be reconstructed. Operator-side existing provider logs/usage/support evidence,
if available, may help resolve execution uncertainty without generation replay.
No automated access to those records was attempted.

The model/free-tier gates, zero-spend requirement, HybridQA external-data blocker,
and pending accuracy/report work from the
[previous state](history/state-before-transport-v5.md) remain in scope. Previous
live-v4 launch instructions are superseded by this stop-and-inspect state.

## Prepared fresh engineering diagnostic (v6)

See [engineering diagnostic commands and limitations](engineering-diagnostic-v6.md).
No live request was executed. Small configurable retry/timeout extensions require
new frozen v6 contracts; v4/v5 artifacts remain historical and untouched.
The earlier request may have executed remotely; the fresh attempt does not resolve
that uncertainty. The diagnostic is not a completed experiment.

## Supported inference providers

Gemini and OpenAI are the supported providers. Puter-specific code, npm dependency, bridge and runner, tests, environment entries, instructions, and the Puter-only pre-integration contract have been removed. Shared experiment architecture, datasets, provider-independent artifacts, Gemini/OpenAI code, and their credentials remain. Active Gemini contracts were refreshed in `experiments/frozen_v10/`; v9 freezes remain historical. No live API calls were made during removal.

## Local Ollama submission integration (2026-11-06)
Native `/api/chat`, stream=false, JSON schema output is now supported alongside
unchanged cloud gates. No cloud calls were made. Explicit settings: context 8192,
reserved output 2048, temperature 0, top_p 1, seed 2626; evidence budget 3000
conservative UTF-8 byte/token upper bounds for all methods. These are estimates,
not tokenizer measurements. Format schema is a grammar constraint, not a message;
message bytes plus 512 framing allowance and reserved output are checked before
dispatch; observed prompt counts are checked on return. Overflow refuses dispatch.
Metadata captures digest, quantization, model info, template and parameters.

The first local tags diagnostic in this agent sandbox failed with EPERM (socket
permission). No more network diagnosis or generation was attempted. The real
inference diagnostic, nine-prediction smoke, official scoring, fixed 20-question
FinQA pilot, runtime extrapolation, other dataset pilots (or full splits with
FULL_SPLITS=1), aggregation, report compilation and packaging are delegated to
`scripts/run_local_submission.sh` in ordinary WSL. Contracts/output directories
are separate; historical cloud uncertain ledgers are untouched. Checkpoints refuse
ambiguous replay. HybridQA stays blocked without linked corpus. No measured local
scores or improvements exist yet; verified Spark and overlap artifacts remain.

Completed local checks: 4 new native-provider checks, 13 existing API checks and
6 OpenAI checks passed. Fresh real-data validation confirmed five datasets;
HybridQA has 3466 blocked dev examples. All nine smoke message bounds plus output
reserve fit (6236–6787 of 8192 conservative tokens). FinQA pilot contains exactly
20 frozen questions. Sixteen separate Ollama contracts were prepared with matching
current source hashes. Source archive prepared under artifacts/ollama_submission.
`bash -n` passed. Report build attempted and blocked by missing `pdflatex`; install
LaTeX in ordinary WSL before the final compilation stage. No local generation,
throughput measurement, official live scores or runtime estimates were fabricated.

Ordinary WSL launch (from this project directory):
`OLLAMA_BASE_URL=http://172.25.80.1:11434 OLLAMA_MODEL=qwen2.5:7b-instruct bash scripts/run_local_submission.sh`
Set `FULL_SPLITS=1` on this same command to run the prepared full splits after the
mandatory smoke and FinQA pilot. Cached completed requests are reused; uncertain
requests remain blocked for inspection. No contract or ledger deletion is needed.

## Urgent bounded submission checkpoint (2026-11-07)

Host process inspection found no old orchestration or child inference runner.
FinQA dev: 2649 rows, 883 per method, 2469 unique completed ledger requests.
Official rescoring of saved rows completed without inference: execution accuracy
ordinary 0, dependency 2/883, length matched 0. Partial test: 162 rows, 54 per
method, 150 completed unique requests and one inflight request; original manifest
incorrectly says completed. Preserve the original checkpoint and use
`artifacts/bounded_submission/checkpoint_audit.json` for verified status.
No inflight records were cleared. No prediction migration was attempted.

Final bounded scope: TAT-QA/TAT-HQA/MultiHiertt 20 dev questions each, ConvFinQA
22 turns in complete conversations, seed 2626. All pilot frozen IDs excluded;
zero pilot overlap. Prior selection artifacts preserved under pre_final_freeze.
Two independent dataset subprocesses use separate exclusive-lock SQLite ledgers;
turns and per-method predicted history remain sequential. Frozen model digest,
prompts, schema, evidence cap and generation settings are retained. New dispatch
stops after 3.5h. Interruption and deadline tests pass; existing 61 tests pass.

Exact ordinary WSL launch: `bash scripts/run_bounded_submission.sh` from final.
Uses the existing .env local Ollama URL; no cloud service or server restart.
Windows: after old requests have drained, run Ollama with OLLAMA_NUM_PARALLEL=2,
OLLAMA_MAX_LOADED_MODELS=1, and the existing WSL-reachable OLLAMA_HOST binding.
No WSL runner remains, but Windows-side active request state was not observed.

Measured LaTeX now includes full FinQA dev scores/status counts, paired clustered
bootstrap, actual invalid examples, verified Spark measurements and overlap.
Bounded inference remains pending. HybridQA remains blocked. TeX installation
attempt failed because sudo requires a password; launcher installs compiler and
PDF utilities interactively, compiles after scoring and renders pages for visual
inspection. Author/affiliation still need completion. No final PDF exists yet.

## Bounded evaluation completed (2026-11-07, final recovery)

Confirmed initial blocker: OLLAMA_BASE_URL absent in all four run environments,
producing local_ollama_base_url_required before any ledger or inference request.
Original manifests are preserved in artifacts/bounded_submission/before_resume.
The recorded endpoint http://172.25.80.1:11434 was reachable, model digest matched,
and one real TAT-QA diagnostic was saved and reused by exact request identity.
No Python inference code, frozen contract, selected ID or model setting changed.
Both shell launchers now provide explicit local-only endpoint/model defaults.

All four original bounded runs completed using separate locked ledgers and at
most two independent dataset workers. FinQA was not regenerated. Final coverage:
TAT-QA 60/60 (50 invalid, 10 abstain); TAT-HQA 60/60 (36 invalid, 24 abstain);
MultiHiertt 60/60 (22 invalid, 38 abstain); ConvFinQA 66/66 (44 invalid, 22 abstain).
ConvFinQA has six complete conversations, 22 ordered turns. Zero missing outputs,
zero infrastructure failures, zero uncertain/inflight requests. Unique completed
requests: 60, 58, 57, 62 respectively (identical method requests may share cache).
All official subset accuracy/F1 scores are zero, for every method; no executable
answers succeeded. Full official metrics, counts and scorer hashes are retained.

Output audit: all 1344 original FinQA-dev malformed rows were JSON and broadly
schema-valid but violated the stricter kind-specific executable-plan contract.
Also audited 92 partial-test, 35 pilot and 8 smoke malformed rows with the same
finding. No valid executable plan was shown to have been rejected. The broad
schema is underconstrained relative to the interpreter; this shared limitation
helps explain model failures but does not justify reinterpreting outputs or
changing old scores. No corrected inference reruns were created or pooled.

Original FinQA manifest/results/cache/metrics SHA256 hashes match before/after.
Report now distinguishes full FinQA dev and four bounded development subsets,
reports coverage/failures, paired uncertainty and real failures, and explicitly
keeps HybridQA blocked. Table split into compact score and status tables; final
PDF compiled to five pages, table pages visually inspected, no overfull warnings.
Author/affiliation placeholders remain and must be filled by the submitter.
Final PDF: report/main.pdf. Source and measurements under bounded_submission;
these archives are distinct from the compiled PDF. All inference runners exited.

## Revised local evaluation completed

Preserved the original PDF/contracts/source bundle under revised_evaluation_v1/
original_submission; original predictions and ledgers remain in their original
folders. A seed-2626 sample of 12 original failures per dataset, including FinQA,
is classified in failure_sample_audit.json. Broad schema/kind mismatch, missing
fields, evidence/span errors and abstention were observed. No gold answer or
reference program repaired any output.

Fixed TRAIN diagnostics used two selected questions/groups per dataset (seven
turns in two ConvFinQA conversations). Native kind-specific anyOf schemas align
required/allowed fields with strict validation. Version 1 exceeded the conservative
context budget. Version 2 compact instructions yielded executable TAT-QA training
outputs and completed a fresh 40-question dev comparison: O/D/L executable counts
14/6/13, all official F1 zero. Version 3 adds a training-motivated prior-step rule
and illustration; training plans still failed. Separate direct TRAIN baselines
showed some correct auxiliary numeric answers for FinQA/ConvFinQA and some correct
MultiHiertt answers, despite plan-production failures. These are not official
FinQA/ConvFinQA program scores.

Versions 4/5 are explicit restricted single-operation arithmetic ablations, not
general multi-step reasoning: schema forbids prior-step operands. Version 4 hit
context guards; version 5 shortened instructions with model, evidence cap and
generation settings unchanged. Six positive/negative schema tests passed. V5
passed the executable TRAIN gate for FinQA, TAT-QA, TAT-HQA and ConvFinQA; all
expanded dev IDs were frozen first. Identical instructions/schema/settings/digest
were verified across datasets/methods; all saved request hashes were validated.

Final v5 development coverage (all three methods combined):
FinQA 40 questions, 120 outputs, 27 local executions, 3 abstentions, 90 invalid;
TAT-QA 40 questions, 120 outputs, 27 local executions, 12 abstentions, 81 invalid;
TAT-HQA 40 questions, 120 outputs, 44 local executions, 2 abstentions, 74 invalid;
ConvFinQA 40 complete conversations/141 ordered turns, 423 outputs, 124 local
executions, 13 abstentions, 286 invalid. Of the ConvFinQA local executions, 36
lack a supported official export and score zero. All four runs complete; zero
missing/infrastructure-failed outputs. FinQA is an explicitly user-authorized
OVERLAPPING 40-question rerun: no unused original dev questions remain. Other
expanded subsets exclude original evaluations and prior revised frozen selections.

Official execution/program scores remain zero on new FinQA/ConvFinQA; TAT-HQA
EM/F1 zero; TAT-QA F1 is .0045 O, .0045 D, zero L, with zero exact matches.
Coverage gains do not imply accurate answers or packing superiority. Original
full FinQA artifacts match their pre-recovery SHA256 hashes, and original zero-score
results remain visible. MultiHiertt v5 TRAIN has three abstentions and three
invalid evidence references; it is blocked from expanded plan scoring. HybridQA
still lacks a required genuine linked table and remains unevaluated. No corpus
acquisition attempted. Paired document/conversation bootstrap summaries are kept
per version/dataset; no independent pooling across shared sources.

Report rebuilt to nine pages; author names Pushpendra Singh and Badri Bishal Das
added as provided (no affiliation supplied). Title and revised score/failure
pages visually inspected; no overfull-box warnings. Final PDF is report/main.pdf;
revised bundle is separate from the preserved original submission bundle.

## Urgent grounded recovery repair (2026-11-07)

Diagnosed saved v5 predictions directly: long source IDs, copied instruction placeholders, invalid offsets/numeric slices, unrelated constant calculations, plus one-operation capacity restriction. Added separate opt-in grounded answer mode with short IDs, exact-quote resolution and up to 16 operations. Prior modes and measured results are preserved. New runner freezes separate recovery dev contracts, compares direct ordinary baseline to grounded ordinary/dependency, retains failed/missing denominators, scores with official adapters and rebuilds the PDF. Live inference is blocked in this tool session: both local Ollama endpoints refuse connections and Windows invocation fails at WSL socket binding. No improved accuracy claimed. See docs/urgent-recovery.md for launch and limitations. PDF rebuilt to six pages with concise final v5 results and measured error counts; prior nine-page PDF and complete generated table archived under grounded_recovery_v1/before_report.

Verification: all 68 unittest checks passed after edits stopped (44.025 seconds), including five new grounding checks. Separate mocked grounded freeze/request/ledger/parser/official-scoring integration passed. Shell syntax and Python compilation passed. Final LaTeX rebuild passed, six pages, no overfull/warning matches; page five visually inspected. Recovery launcher connectivity preflight failed cleanly with curl exit 7 before any live inference. Historical scores are unchanged.
