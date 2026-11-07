> Current status: live smoke v4 stopped with an uncertain generation attempt.
> Do not replay it. Diagnostics now use v5 contracts; historical v4 launch commands
> below are superseded. See [the failure audit and offline next command](docs/state.md).

# Numerical reasoning with dependency-preserving evidence packing

One shared pipeline across FinQA, TAT-QA, ConvFinQA, HybridQA, TAT-HQA and
MultiHiertt. Research question: **with the same model and evidence budget, does
preserving evidence dependencies improve answer quality over ordinary packing?**

Implementation is prepared for local and later live acceptance. **No successful
live predictions or model accuracy results are established.** The report is a
draft. This implementation session made no authenticated provider calls and
spent no credits. Existing historical artifacts remain separate.

Start here, from `final`:

```bash
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python -m unittest discover -s tests -v
```

The final local suite passed **52/52 tests**; the mock smoke completed nine requests
and replayed them with nine cache hits and zero new generations. See
[current real-data audit](docs/data-integration-v3.md).

Then follow [the complete ordinary-WSL testing and experiment sequence](docs/final-testing.md).
It covers local validation, frozen mock replay, the later three-question live
smoke, 20-question pilot, per-dataset runs, ablations, Spark, aggregation and report
compilation. Live commands are preparation for your later execution, not commands
already run by the agent. [Current state](docs/state.md), [completed work and checks](docs/plan.md),
[original design](docs/proposal.md), [implementation decisions](docs/implementation.md),
and [data acquisition](docs/acquisition.md) give the details.

| Dataset | Implemented | Local input checks | Remaining gate |
|---|---|---|---|
| FinQA | Reader, arithmetic export, official scoring | All 883 dev records; training fixtures | Live acceptance |
| TAT-QA | Reader, span/list/count/scale outputs, official scoring | All 1,668 dev questions; training fixtures | Live acceptance; use test-gold's own IDs |
| ConvFinQA | Ordered reader, predicted state, cumulative program export, official scoring | All 1,490 dev turns; exact official turn-ID match | Live ordered-history acceptance; hidden-test scoring |
| HybridQA | Linked reader and official EM/F1 | Real train/dev/test questions inventoried: 62,682 / 3,466 / 3,463 | All blocked by absent linked corpus |
| TAT-HQA | Hypothetical reader, question-grounded overlays, official scoring | All 824 hypothetical dev questions; training fixtures | Live acceptance; hidden-test scoring |
| MultiHiertt | Real HTML/merged-cell reader, span/program output, official scoring | All 7,830 train / 1,044 dev / 1,566 test inputs checked | Test labels hidden; 61 unused cached-description mismatches reported |

MultiHiertt data is now read from `../MultiHiertt_data/multihiertt_data`; no download
is needed. HybridQA's `released_data` contains questions and annotations, not its
linked tables/passages. No real `tables_tok`/`request_tok` corpus was found in the
supplied locations or workspace. See [verified findings and counts](docs/data-integration-v3.md)
and [configurable paths/acquisition](docs/acquisition.md). All gold MultiHiertt
references resolve through HTML geometry. The 61 cached-description mismatches
remain visible in the audit and are excluded from inference, as before.

The active local contracts for the existing provider routes are in
`experiments/frozen_v10/` and `experiments/contracts_v9.json`; prior v4-v9
contracts and artifacts remain historical. No HybridQA inference contract is
created without its corpus.

The engine includes deterministic BM25 retrieval; ordinary, recursive dependency,
and approximate length-matched neighbor packing; validated extraction, arithmetic,
aggregates, counting, comparison, selection, and hypothetical changes; and separate
predicted conversation histories per method. Inference uses an allowlist of the
current question and packed evidence. Labels and future turns stay outside it.
Unsupported official exports are recorded as failures rather than given invented
identity programs. See [evaluator behavior and limitations](docs/implementation.md).

Gemini `gemini-3.8-flash` is now frozen with low thinking and no sampling overrides.
See [the exact migration changes and official sources](docs/gemini-migration-v4.md). The supported inference providers are Gemini and OpenAI. Both use bounded retries, quota stops, redacted diagnostics, raw/parsed result storage, provider/model/settings recording, and a durable SQLite request ledger. Runs remain model-pinned, with a $0 spending ceiling and provider-specific account eligibility checks. See [the testing and experiment sequence](docs/final-testing.md) for local checks and later operator-run live procedures.

The ordinary-WSL v3 smoke stopped at countTokens: HTTP 404, old model unavailable
for new users, zero completed requests and zero generation attempts. Its directory
is preserved. The new model keeps the existing v1beta countTokens/generateContent
API and JSON schema. New caches start empty. No live APIs were called here.

Keep `.env` private. The scripts parse allowed literal assignments without sourcing
a shell. For Gemini, configure `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.8-flash`, and
`GEMINI_FREE_TIER_CONFIRMED=gemini-3.8-flash:YYYY-MM-DD` only after checking that
key's project has Free tier, disabled/unlinked billing, access to this exact model
and enough request/token quota for the
whole bounded run. Public free-tier pricing does not prove account eligibility.
The agent did not set your attestation or change private `.env`. Recheck on a new UTC date or key/project change. The historical
OpenAI credential was exposed and must be revoked/replaced before optional OpenAI
use; that route additionally requires an explicit model and dated free-credit
confirmation. No key is included in the delivery archive.

Spark preparation writes deduplicated documents, questions, facts and partitioned
Parquet, checks joins/edges, and computes overlap. Python supplies the correctness
reference. Java and PySpark are installed, but local Spark startup failed with
`SocketException: Operation not permitted` in this restricted agent environment.
A saved small ordinary-WSL acceptance run matches the Python result; full repeated
performance benchmarks remain pending. See [current state](docs/state.md). Local Spark on one laptop
is not a distributed-cluster experiment.

The earlier source archive is historical; the data integration update is packaged
as `artifacts/delivery/nrqa-source-data-v3.tar.gz`.

The [LaTeX draft](report/main.tex) copies the supplied ACL style into `report/`,
leaving the original unchanged. `pdflatex`, `bibtex` and `latexmk` are absent here.
Main results, uncertainty, error analysis, ablation effects, provider usage/latency,
and Spark measurements are explicitly pending. No accuracy gain, speedup, cost or
significance claim is made.

Use the existing environment; nothing was installed. `requirements-local.txt`
records local versions for optional installation in an isolated environment.
Old milestone descriptions are archived under `docs/history/`; their stop rules
and next-action instructions are superseded by the current implementation scope.
