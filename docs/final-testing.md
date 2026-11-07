> Current status: live smoke v4 stopped with an uncertain generation attempt.
> Do not replay it. Diagnostics now use v5 contracts; historical v4 launch commands
> below are superseded. See [the failure audit and offline next command](state.md).

# Final ordinary-WSL testing and experiment sequence

## Supported providers and current state

Gemini and OpenAI are the supported inference providers. The frozen Gemini contracts in `experiments/frozen_v10/` use the cleaned provider code; v9 contracts are retained as history. Code changes require a newly frozen contract before inference. Local validation, delivery checks, and mock runs do not call provider APIs. Live experiments remain operator-run only after the account, quota, and zero-spend gates in [README](../README.md).

The remaining sections describe prior Gemini/v4 and historical data/Spark tasks. Live experiments and final acceptance have **not** run. No installation is needed for the existing Python checks. The report stays a draft until measured results, interpretation and a verified PDF are incorporated.

## 1. Local correctness and input readiness

```bash
cd /home/p_2626/BigDataEndSem/final
export PYTHONPATH="$PWD/src"
export PYTHONDONTWRITEBYTECODE=1
NRQA_PY=/home/p_2626/bigdata-env/bin/python
"$NRQA_PY" -m unittest discover -s tests -v
"$NRQA_PY" scripts/validate_local.py --out artifacts/model_migration_v4/local_validation.json
"$NRQA_PY" scripts/check_delivery.py
```

`validate_local.py` checks the four existing dev readers, all 10,440 real MultiHiertt
records and all 69,611 HybridQA question records. MultiHiertt is present under the
configured sibling path. Its 61 stale cached-description coordinates are listed,
while all annotated table/text evidence references resolve. HybridQA remains blocked
by missing tables_tok/request_tok evidence, not missing questions. Acquire only the
missing genuine linked corpus using [acquisition.md](acquisition.md), then rerun.
No fixtures substitute for real-data validation. Optional directory overrides are
`NRQA_MULTIHIERTT_ROOT`, `NRQA_HYBRIDQA_QUESTIONS` and `NRQA_HYBRIDQA_CORPUS`.
If dependencies need changing, create `final/.venv` or a separate environment and
install `requirements-local.txt` there; do not modify the shared environment or
upstream repositories. Java is separately required for Spark.

## 2. Check the v4 contracts and mock resumption

`experiments/contracts_v4.json` lists 21 active contracts in `frozen_v4` and hashes
all 39 historical original/v3 contracts. The checker validates contract/code/source/
input hashes. Changed code/data/config requires a new version and output directory;
never overwrite a frozen live contract. The failed `live_smoke_v3` is unchanged.
Active smoke contract: `d2195323d9021aa425001214260e69818f25b73f201055ae756f1624dd7f49f7`.

The v4 prepare/mock checks are already complete. To reproduce the generic offline
mock path later (synthetic abstentions/counts, no credentials or live calls):

```bash
"$NRQA_PY" -m nrqa.experiment run experiments/frozen_v4/smoke.json artifacts/prepared_smoke_v4 --mode prepare
"$NRQA_PY" -m nrqa.experiment run experiments/frozen_v4/smoke.json artifacts/mock_fixture_smoke_v4 --mode mock
"$NRQA_PY" -m nrqa.experiment run experiments/frozen_v4/smoke.json artifacts/mock_fixture_smoke_v4 --mode mock
"$NRQA_PY" -m nrqa.experiment evaluate experiments/frozen_v4/smoke.json artifacts/mock_fixture_smoke_v4
```

`artifacts/mock_smoke_v4` instead records the Gemini adapter with fake HTTP, tested
locally to cover real REST serialization. Keep it separate from the generic mock
provider above. Its first run made nine fake generations and fresh count calls;
replay reused nine predictions with zero new generation/count calls. No real
provider requests or measured provider tokens are involved. Each method retains
all three questions in its denominator. Explicit smoke IDs override sample_size 20.

Saved evidence: `artifacts/model_migration_v4/contracts_check.json`,
`preserved_sha256.json`, `delivery_checks.json`, `mock_first_manifest.json`,
`mock_replay_manifest.json`, `mock_replay_check.json` and `unit_tests.txt`.
All new contracts preserve the v3 IDs, source/input hashes, prompts and schemas;
only model/settings/code hashes and resulting contract digests change.

The historical MultiHiertt prepare check in `artifacts/prepared_multihiertt_pilot_v3`
has all 20 real questions and 60 method rows. For a new preparation under current
code use `experiments/frozen_v4/multihiertt_pilot.json` and a fresh
`artifacts/prepared_multihiertt_pilot_v4` path. The full data audit still reports
four train and 57 test unused cached-description coordinate issues; dev has none.
Descriptions remain excluded from prediction evidence.

HybridQA remains blocked. Follow `docs/acquisition.md`: clone
`https://github.com/wenhuchen/WikiTables-WithLinks` to `data/WikiTables-WithLinks`,
then follow that repository's archive download/unpack instructions if needed.
Verify actual `tables_tok/TABLE_ID.json` and `request_tok/TABLE_ID.json` for every
assigned table; clone success alone is insufficient. Tables must contain linked
header/body cells and request files must map every link to nonempty passage text.
Then run the documented validation, pilot freeze and delivery check. This step
has not been performed. Traced answer annotations and fixtures are not evidence.

## 3. Small Spark acceptance, then measurements

Run a real-record correctness comparison first (no inference):

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/p_2626/bigdata-env/bin/python scripts/prepare_data.py experiments/finqa_pilot.json experiments/tatqa_pilot.json experiments/convfinqa_pilot.json experiments/tathqa_pilot.json experiments/multihiertt_pilot.json --out artifacts/spark_acceptance_v3 --limit 5
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/p_2626/bigdata-env/bin/python scripts/measure_resources.py --out artifacts/spark_acceptance_v3/resources.json -- /home/p_2626/bigdata-env/bin/python scripts/prepare_data.py --out artifacts/spark_acceptance_v3 --spark --master 'local[1]'
```

Run from `final`. These use all five ready datasets and a fresh v3 directory.
The preparation script takes the first five source questions/turns per config,
not the frozen pilot selection: expect 25 questions in total. HybridQA remains
blocked and is not silently counted as tested. These two commands are pending.

Require `spark_measurement.json: equals_python=true`, matching canonical join hashes,
edge counts and overlap pairs. Startup failed with socket EPERM in the agent
sandbox; this ordinary-WSL step is unverified. Do not describe it as passed yet.

For benchmark sizes, limits apply per source **question/turn**, not documents or
new independent examples. Actual counts and unique documents are saved. No copied
records are added. Run each size three times if practical, saving fresh output
paths and distinguishing JVM cold starts from repeated OS page-cache runs:

```bash
for n in 100 1000; do
  "$NRQA_PY" scripts/measure_resources.py --out "artifacts/python_${n}.json" -- "$NRQA_PY" scripts/prepare_data.py experiments/finqa_full_dev.json experiments/tatqa_full_dev.json experiments/convfinqa_full_dev.json experiments/tathqa_full_dev.json --out "artifacts/size_${n}" --limit "$n"
  "$NRQA_PY" scripts/measure_resources.py --out "artifacts/spark_${n}_local1.json" -- "$NRQA_PY" scripts/prepare_data.py --out "artifacts/size_${n}" --spark --master 'local[1]'
  "$NRQA_PY" scripts/measure_resources.py --out "artifacts/spark_${n}_local4.json" -- "$NRQA_PY" scripts/prepare_data.py --out "artifacts/size_${n}" --spark --master 'local[4]'
done
"$NRQA_PY" scripts/prepare_data.py experiments/finqa_full_dev.json experiments/tatqa_full_dev.json experiments/convfinqa_full_dev.json experiments/tathqa_full_dev.json --out artifacts/size_full
"$NRQA_PY" scripts/measure_resources.py --out artifacts/spark_full_resources.json -- "$NRQA_PY" scripts/prepare_data.py --out artifacts/size_full --spark --master 'local[4]'
du -sh artifacts/size_*/parquet
```

Resource helper samples Python/JVM process-tree RSS every 0.1 seconds. Summed RSS
can double-count shared pages and miss short peaks. Spark event logs are saved in
`OUT/spark-events` for stage/task/spill analysis; inspect them using Spark History
Server if available. Local `[1]`/`[4]` means one laptop, not a distributed cluster.

## 4. Overlap audit before any final scoring

The following operates on inputs only. Add newly acquired datasets and train/test
configurations as needed; preserve official splits. For cross-split inspection,
copy a config, set its real `source`, `split` and ZIP `member`, then pass it here.
No data is merged into training and no labels are used. Exact table/source and
question-table hashes complement approximate 5-gram MinHash/Jaccard candidates.
The near-pair cap and approximate recall limitations are reported.

```bash
"$NRQA_PY" scripts/audit_overlap.py experiments/finqa_full_dev.json experiments/tatqa_full_dev.json experiments/convfinqa_full_dev.json experiments/tathqa_full_dev.json --out artifacts/overlap_dev.json
```

Keep per-dataset scores. Do not pool overlapping datasets as independent samples.
Use document/conversation bootstrap intervals; any cross-dataset aggregate needs
shared-source clustering, which this script deliberately does not pretend to infer.

## 5. Later live three-question smoke, then replay

Before these commands, inspect the owning project's current Free tier, disabled/
unlinked billing, exact `gemini-3.8-flash` availability and enough request/token
headroom in AI Studio. Put a valid key and the dated attestation in private `.env`
as described in README. Set `GEMINI_MODEL=gemini-3.8-flash` explicitly and only
after these checks set `GEMINI_FREE_TIER_CONFIRMED=gemini-3.8-flash:YYYY-MM-DD`
with today's UTC date. Public free pricing is not account eligibility. The agent
did not read/change private `.env` or set an attestation. If free access/quota is
absent, stop; no paid fallback is allowed. Do not source `.env` or print it. Do not enable paid billing.
An attestation is operator evidence and expires each UTC day. Exact model is frozen;
no alternate model/provider will be selected automatically.

```bash
"$NRQA_PY" -m nrqa.experiment run experiments/frozen_v4/smoke.json artifacts/live_smoke_v4 --mode live
"$NRQA_PY" -m nrqa.experiment evaluate experiments/frozen_v4/smoke.json artifacts/live_smoke_v4
```

Inspect `manifest.json`, redacted `error_details`, `current_input.json`, and saved
results. If HTTP 404 repeats, identify the method/stage/provider message before
any correction; [gemini-migration-v4.md](gemini-migration-v4.md) records the latest failure and migration.
Quota, timeout or inflight records are checkpointed. Do not delete a ledger or
retry uncertain dispatch blindly. A stopped run can be scored with explicit
missing entries, but is not a completed paired experiment.

Only after **completed** smoke, repeat exactly this command to check cached replay:

```bash
"$NRQA_PY" -m nrqa.experiment run experiments/frozen_v4/smoke.json artifacts/live_smoke_v4 --mode live
```

Require nine reused logical predictions and zero new generation calls, consistent
resolved model, valid outputs or explicitly counted failures. Manually trace one
real prediction from selected evidence through validation/execution/export/scoring.
Classify failures without gold-driven repairs. Do not tune and claim improvement
on the smoke set.

## 6. Fixed 20-question three-method FinQA pilot

The pilot uses seed 2626 and excludes the three smoke IDs. Three methods × 20 =
60 logical generations; at most 180 generation attempts. Account quota must cover
token-count requests too (separately bounded to 1,000/invocation). Compare only on
the exact same provider/model. No inference has been run for this pilot.

```bash
"$NRQA_PY" -m nrqa.experiment freeze experiments/finqa_pilot.json experiments/frozen_v4/finqa_pilot.json
"$NRQA_PY" -m nrqa.experiment run experiments/frozen_v4/finqa_pilot.json artifacts/live_finqa_pilot_v4 --mode live
"$NRQA_PY" -m nrqa.experiment evaluate experiments/frozen_v4/finqa_pilot.json artifacts/live_finqa_pilot_v4
```

Review invalid/abstain/missing/API/unsupported-export counts, actual evidence
lengths and C's matching gap before interpreting answer quality. A small pilot
is exploratory. Freeze a new version before any prompt or operation change.

## 7. Per-dataset fixed subsets, full dev and final test options

Run only after data readiness, smoke acceptance and quota feasibility. HybridQA
and ablation_no_links are excluded from these loops until the genuine corpus is
available and validated; then create and register their new contracts separately. The pilot
configs select 20 questions for each nonconversation dataset; ConvFinQA selects
five complete conversations, with actual turn count recorded. Missing data must
be acquired before freezing. Do not skip a failed dataset while calling a study
six-dataset validated.

```bash
for dataset in tatqa convfinqa tathqa multihiertt; do
  "$NRQA_PY" -m nrqa.experiment freeze "experiments/${dataset}_pilot.json" "experiments/frozen_v4/${dataset}_pilot.json"
  "$NRQA_PY" -m nrqa.experiment run "experiments/frozen_v4/${dataset}_pilot.json" "artifacts/live_${dataset}_pilot_v4" --mode live
  "$NRQA_PY" -m nrqa.experiment evaluate "experiments/frozen_v4/${dataset}_pilot.json" "artifacts/live_${dataset}_pilot_v4"
done
```

Use the same pattern with `*_full_dev.json` or `*_full_test.json` and **new run
paths** for full splits. Full runs are options, not a promise of free quota or
runtime feasibility. Before calls, freeze each selected configuration:

```bash
"$NRQA_PY" -m nrqa.experiment freeze experiments/finqa_full_test.json experiments/frozen_v4/finqa_full_test.json
"$NRQA_PY" -m nrqa.experiment run experiments/frozen_v4/finqa_full_test.json artifacts/live_finqa_full_test_v4 --mode live
"$NRQA_PY" -m nrqa.experiment evaluate experiments/frozen_v4/finqa_full_test.json artifacts/live_finqa_full_test_v4
```

Repeat for the remaining datasets only when feasible. ConvFinQA, HybridQA,
TAT-HQA and possibly MultiHiertt test require official external scoring when labels
are hidden; the local wrapper reports `hidden_labels` and still exports submissions.
TAT-QA final uses its 1,663-question released test-gold version, never the 1,669
original public-test IDs. Do not tune prompts on final test answers.

## 8. Component removals and direct baselines

A1 (no dependency closure) is already the ordinary main result; reuse it.
Other configs remove headers (FinQA), linked passages (HybridQA), predicted
history (ConvFinQA), or hypothetical overlays (TAT-HQA). These are impaired
component diagnostics. `direct_baseline` uses ordinary packing with direct
answers; `no_executor` uses dependency packing with direct answers. Their FinQA
numeric accuracy is auxiliary and has no official program-equivalence score.

```bash
for name in ablation_no_headers ablation_no_history ablation_no_overlay direct_baseline no_executor; do
  "$NRQA_PY" -m nrqa.experiment freeze "experiments/${name}.json" "experiments/frozen_v4/${name}.json"
  "$NRQA_PY" -m nrqa.experiment run "experiments/frozen_v4/${name}.json" "artifacts/live_${name}_v4" --mode live
  "$NRQA_PY" -m nrqa.experiment evaluate "experiments/frozen_v4/${name}.json" "artifacts/live_${name}_v4"
done
```

## 9. Aggregate measured results and finish the report

Aggregation rejects mock input unless `--allow-mock` is explicitly used for an
engineering check. Keep provider/model identity in every row. No unlabeled pooled
model score is created. The paired bootstrap uses 1,000 document/conversation
resamples and seed 2626. Review exact status denominators, incomplete-pair attrition,
matching gaps and the official/raw score distinction.

```bash
"$NRQA_PY" scripts/aggregate_results.py artifacts/live_finqa_pilot_v4 --out artifacts/report_live_v4
"$NRQA_PY" scripts/plot_results.py artifacts/report_live_v4/summary.json --out report/generated/pilot_scores_v4.pdf
```

Pass all completed per-dataset/diagnostic run directories to aggregation for the
full CSV. The generated `results.tex` may need layout editing for two columns;
inspect it before replacing `report/generated/results.tex`. Use only live measured
rows, never mock scores. Add uncertainty and failure/error analysis, resource
measurements, actual usage and quota limitations; update the abstract/discussion.
Fill author/affiliation. Do not describe the draft as final yet.

`pdflatex`, `bibtex` and `latexmk` are missing in the agent environment. After
installing a suitable TeX distribution in ordinary WSL, compile with:

```bash
make -C report
```

Inspect the resulting PDF, citations, tables and overfull-box warnings. Then rerun
local tests and delivery checks, save a measured-result ledger and prepare a new
source bundle:

```bash
"$NRQA_PY" -m unittest discover -s tests -v
"$NRQA_PY" scripts/check_delivery.py
"$NRQA_PY" scripts/package_delivery.py --out artifacts/delivery/nrqa-source-model-v4.tar.gz
```

For this model update, use `artifacts/delivery/nrqa-source-model-v4.tar.gz`; keep earlier archives historical.

The archive excludes `.env`, `api.txt`, raw data, provider ledgers and upstream
repositories. Its manifest lists source hashes. It does not certify inaccessible
Git history. Include reviewed final result artifacts separately without credentials.
