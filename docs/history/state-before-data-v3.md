# Current delivery state

Updated 2026-11-06. Implementation and offline delivery preparation are complete
within the available data/environment boundary. **Live predictions, final
end-to-end acceptance, model accuracy, Spark equivalence/performance and the
compiled report are not established.** The report is a draft. This implementation
session made zero authenticated provider requests, zero live inference calls,
no dependency installations and no upstream/raw-data edits.

The research question remains: with the same model and evidence budget, does
preserving evidence dependencies improve answers compared with ordinary packing?
The exact experimental Gemini model remains `gemini-2.5-flash`; no substitute
provider/model was selected. Existing OpenAI support is retained, with no fallback.
The spending ceiling remains $0.

Implemented: six prediction-only readers with separate references; deterministic
BM25 retrieval; ordinary/dependency/approximate-length-matched packing; bounded
source-grounded answer tools; prior-prediction conversation state and cumulative
program export; output conversion and isolated official metrics; free-access gates,
redacted provider diagnostics and durable request/response/cache/resumption;
Python/Spark preparation and overlap tooling; frozen configs; aggregation,
bootstrap and plotting; ACL report source; final testing instructions and source
packaging. See `implementation.md` for semantics and limits.

| Dataset | Reader/input validation | Official scorer/output checks | Ready for later experiment? |
|---|---|---|---|
| FinQA | 883/883 dev; no duplicate IDs/unresolved edges; existing 10 training fixtures | Official arithmetic/symbolic contracts and failure denominator | Yes, pending provider/live acceptance |
| TAT-QA | 1,668/1,668 dev; training fixture mutation tests | Official EM/F1/scale, numeric zero, spans/lists | Yes; final released test-gold has 1,663 own IDs |
| ConvFinQA | 1,490/1,490 dev; all official turn IDs match; complete ordered histories | Official single-number/arithmetic/symbolic functions; cumulative predicted programs; hidden export | Yes; final private test needs external scoring |
| HybridQA | Synthetic linked table/passage fixture only | Official EM/F1 function contracts; dev subgroup integration prepared | Blocked by missing real linked corpus |
| TAT-HQA | 824/824 hypothetical dev; no duplicate IDs/unresolved edges | Official EM/F1/scale class, bypassing CLI counter typo | Yes; hidden test remains external scoring |
| MultiHiertt | Synthetic documented HTML fixture only; merged geometry/ancestors | Official program/span/mixed functions and invalid-output policy | Blocked by missing raw data/schema confirmation |

All ready rows still require later live acceptance. Missing datasets remain part
of the project and must be reported as unavailable if acquisition fails, not
silently removed from a six-dataset claim.

Local evidence:

- `artifacts/implementation/tests.txt`: **44/44 tests passed** in the final unittest run with detailed test names,
  including all six scorers, firewall mutation, budget and tool tests, cache and
  resumption, model pins, hidden submission export, Python preparation and API mocks.
- `artifacts/implementation/local_validation.json` and summary: full available dev
  reader counts, source hashes, zero duplicate IDs/unresolved edges, sampled budgets.
- `artifacts/mock_smoke_v2/manifest.json`: 9/9 mock requests completed; cached replay
  has 9 hits and zero new generations. Metrics keep three abstentions per method
  and a denominator of three. This is not model accuracy or provider token evidence.
- `artifacts/preparation_fixture/python_reference.json`: 20 joins, 335 dependency
  edges, zero unresolved edges on first five questions/turns per available dev source.
- `artifacts/implementation/overlap_fixture.json`: input-only bounded overlap check
  on first 50 questions/turns per source; full audit remains a later command.
- `artifacts/implementation/spark_startup.log`: JVM failure caused by
  `java.net.SocketException: Operation not permitted (Socket creation failed)`;
  no Spark task completed and no Python/Spark equivalence or speedup is claimed.
- `artifacts/implementation/frozen_readiness.json`: 18 final code/input/config
  contracts. The five-conversation ConvFinQA pilot contains **12 turns**, not 20.
- `artifacts/implementation/delivery_checks.json`: source freeze/citation/style
  checks and absent TeX tools. Environment versions are in `requirements-local.txt`
  and `artifacts/implementation/environment.json`.
- `artifacts/delivery/nrqa-source.tar.gz` plus its manifest: allowlisted source draft,
  with credentials/raw data/provider ledgers/upstream repositories excluded.

HTTP 404: the saved historical manifest records metadata success, zero generation
attempts and one token-count attempt. The old handler discarded its error body.
Current construction matches the documented endpoint form, so no justified model
or API-version change was made. Error messages/status/request-ID/stage now survive
with redaction. Live access and the deeper 404 cause remain unverified; see
`provider-404.md`. Ordinary WSL connectivity is already established and was not
re-diagnosed. The historical OpenAI key was exposed; revoke/replace it before any
optional OpenAI use. Its eligibility is not assumed from a working key.

First command, from `final`:

```bash
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python -m unittest discover -s tests -v
```

The complete ordered final test/experiment commands are in `final-testing.md`.
Acquire missing inputs per `acquisition.md`; use the current frozen files for
unchanged source/code, or create new versioned freezes before changed-code live
runs. All current inference examples are free of labels/future turns by construction;
training fixtures still intentionally carry separate labels for contract testing.

External blockers: exact free model/token-count/generation access; real HybridQA
and MultiHiertt evidence; ordinary-WSL Spark execution; TeX tooling and PDF review;
external hidden-test scoring where required. Full-run quota/runtime feasibility and
hosted-model contamination remain unknown. The deadline recorded previously is
8 November 2026; submission time/rubric specifics remain unverified.

The report already contains the problem, literature, dataset scope, architecture,
packing mechanism, protocol, reproducibility and limitations. Main answer scores,
confidence intervals, ablation effects, error analysis, actual evidence length and
matching gaps, model token/latency/quota observations, and Spark resource results
must be incorporated from real measurements before final submission. Update the
abstract/discussion and author details, compile and inspect the PDF, then package
reviewed results separately. No invented score, improvement, runtime, cost or
significance claim has been inserted.
