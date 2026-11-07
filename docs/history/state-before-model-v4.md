# Current project state — data integration v3

Updated 2026-11-06. Real data discovery and reader reconciliation are complete for
the supplied locations. **No inference APIs, packages or downloads were used.**
Raw data and upstream repositories remain unchanged. Live predictions, model
accuracy and report compilation remain unverified. The saved small Spark acceptance
and development overlap audit are verified below; larger Spark benchmarks remain pending.

MultiHiertt is present and integrated. HybridQA question files are present, but
its linked evidence corpus is genuinely absent from the inspected locations and
workspace. Earlier statements that MultiHiertt raw data was missing are superseded.
The earlier source delivery/archive and frozen contracts remain historical.

| Dataset/split | Actual records | Duplicate IDs | Verified readiness |
|---|---:|---:|---|
| HybridQA train | 62,682 | 0 | Questions only; all blocked by missing linked corpus |
| HybridQA dev | 3,466 | 0 | Questions/reference IDs and answers match; all corpus-blocked |
| HybridQA test | 3,463 | 0 | Questions only, hidden labels; all corpus-blocked |
| MultiHiertt train | 7,830 | 0 | All raw inputs/dependencies/gold evidence resolve; four cached-description issues |
| MultiHiertt dev | 1,044 | 0 | All raw inputs, dependencies, geometry and annotations checked |
| MultiHiertt test | 1,566 | 0 | All raw inputs/dependencies checked; hidden labels; 57 cached-description issues |

The four other dev readers still validate: FinQA 883, TAT-QA 1,668, ConvFinQA
1,490 turns and TAT-HQA 824 hypothetical questions. All six use the same reasoning
architecture; this update changes dataset I/O and validation, not the model or
research question. Gemini `gemini-2.5-flash` and the $0 policy remain fixed.

MultiHiertt findings and fixes:

- Actual JSON keys and question types match the documented broad schema. Real
  tables use `td` for headers, so the reader now retains multi-row inferred headers,
  section years and unit changes. Inference uncertainty remains explicit.
- HTML geometry supplies aliases for coordinates inside merged cells. All 19,762
  train and 2,683 dev table evidence references resolve, including eight train
  references to merged interiors. All 6,582 train and 932 dev text references resolve.
- Every table marker resolves: 31,567 train, 4,050 dev and 6,195 test table/text
  links, counted per question context. No duplicate facts, missing dependency edges
  or dependency cycles remain across all 10,440 records.
- Cached table descriptions contain 61 coordinates without HTML cells: four train
  entries affecting four questions and 57 test entries affecting 12 questions.
  They are reported with IDs, not fabricated or silently removed. Descriptions
  remain excluded from prediction inputs; raw context and answer scoring stay usable.
- Actual program outputs require numeric JSON predicted_ans values. The adapter
  now matches the official callback, fixing mixed span/program scoring's numeric
  string TypeError without changing metric functions or tolerances.

HybridQA findings:

- `released_data` has train/dev/test questions, traced annotations and dev references,
  not the required linked tables/passages. All 3,466 dev reference IDs and answer
  strings match the question file.
- Missing resources are `tables_tok/TABLE_ID.json` and `request_tok/TABLE_ID.json`
  for 12,374 train, 3,053 dev and 3,061 test assigned table IDs. These counts overlap
  across splits and must not be summed as distinct corpus tables.
- Every missing filename and blocked question ID is in local_validation.json.
  Passage targets cannot be enumerated until their tables are present. Synthetic
  fixtures and answer-node traces were not substituted for real evidence.

Checks completed:

- **50/50 tests pass**, including six new real-data/path/scoring regressions. Real
  GOLD/COPPER section units, merged coordinates, marker links, reference mutation,
  explicit path overrides and missing-resource coverage are tested.
- `scripts/validate_local.py` audits every available MultiHiertt split and every
  HybridQA question, plus the existing four dev readers. Its code/source hashes
  and exact issues are saved in `artifacts/implementation/local_validation.json`.
- `scripts/validate_data_contracts.py` exports all-ID abstentions for 7,830 train,
  1,044 dev and 1,566 hidden test records. It additionally checks arithmetic/span
  reference round-trips on annotated splits. These are engineering checks using
  reference expectations, **not model predictions or model accuracy**.
- `scripts/check_delivery.py` strictly validates 21 active v3 freezes and checks
  that all 18 historical freezes retain their original hashes. It explicitly
  reports HybridQA as externally blocked. It does not claim full project acceptance.

Active contracts are in `experiments/frozen_v3/`; the registry is
`experiments/contracts_v3.json`. Eighteen replacements preserve prior IDs, prompts,
model, seeds and settings; three new contracts freeze the actual MultiHiertt pilot
(20 questions), full dev and full test. Old `experiments/frozen/` files are untouched
and cannot be run with changed code. Use new v3 output paths as documented.
No HybridQA inference contract is fabricated while evidence is absent.

Detailed findings: [data-integration-v3.md](data-integration-v3.md).
Commands: [final-testing.md](final-testing.md).
Paths/acquisition: [acquisition.md](acquisition.md).
Evidence: `artifacts/data_integration_v3/` and the current local/delivery validation
JSON files under `artifacts/implementation/`.

The small Spark commands previously listed here have completed; verified saved
results and the next live-smoke command are recorded below. HybridQA is excluded
because its evidence is missing; it remains blocked, not passed. Acquire its genuine
corpus using acquisition.md, then rerun validation before freezing its pilot.

Contract/mock milestone completed 2026-11-06:

- `AGENTS.md` is absent; project instructions were read from `Agents.md`.
- All 21 active contracts passed strict code, source, input and contract hash
  validation. All match their current `experiments/*.json` configurations. All 18
  historical freezes retain their hashes. No contract or implementation changed.
- Active smoke: `experiments/frozen_v3/smoke.json`, matching
  `experiments/smoke.json`; contract
  `fd6d6278330dcd28dabee59f1f4f9b005b5437b5ae9212ac54f909d173284974`.
  Source `../FinQA/dataset/dev.json` resolves and its SHA-256 is
  `a847fb7e0d61a3125a1e2909852df6b89f1ee64d2c5ff1bf689e332214deee51`.
  All three selected input hashes match. Explicit IDs take priority over the
  generic `sample_size: 20` field: three questions × three methods = nine rows.
- `artifacts/prepared_smoke_v3/` contains nine prepared rows.
  `artifacts/mock_smoke_v3/` contains nine unique logical predictions, all labeled
  mock. First run: nine new mock calls, zero cache hits. Replay: nine cache hits,
  zero new generation calls and zero new token-count calls; total calls stay nine.
  First/replay manifests are saved separately under `artifacts/final_testing_v3/`.
- Mock evaluation completed for all three methods, retaining three abstentions
  in each denominator. This verifies scoring/export integration only, not model
  accuracy. Usage and token counts are synthetic; no live APIs were called.
- `experiments/frozen_v3/multihiertt_pilot.json` matches
  `experiments/multihiertt_pilot.json`. Its real dev source and selected input
  hashes passed. `artifacts/prepared_multihiertt_pilot_v3/` contains all 20 selected
  questions × three methods = 60 rows, with zero inference calls and no drops.
  Dev has zero coordinate warnings, so none affect selected prediction evidence.
  Existing full-audit warnings remain: four cached-description coordinates in
  four train questions and 57 in 12 test questions. Cached descriptions remain
  outside prediction inputs. The audit was reused after checking its code and
  all three source hashes; it was not rerun unnecessarily.
- Evidence: `artifacts/final_testing_v3/contracts_check.json`,
  `configuration_matches.json`, `mock_replay_check.json` and
  `multihiertt_preparation_check.json` (including exact coordinate warning IDs).
  No packages were installed. Completed unit/full-data checks were not repeated.

Other external blockers remain: exact free-provider/token-count/generation access
(the earlier HTTP 404 cause is unresolved), TeX tools
and PDF review, and external hidden-test scoring. The exposed historical OpenAI
credential must be replaced before optional OpenAI use. No live experiment was run.
The report remains a draft; scores, uncertainty, ablations, error analysis, usage,
latency and Spark performance require real measurements before final submission.

Spark acceptance and development overlap milestone verified 2026-11-06:

- Saved evidence in `artifacts/spark_acceptance_v3/` passes the small acceptance
  comparison: Spark 4.2.0, `local[1]`, `equals_python=true`, 25 questions/turns
  (five each from FinQA, TAT-QA, ConvFinQA, TAT-HQA and MultiHiertt), 14 normalized
  documents, 1,925 facts, 5,733 dependency edges, zero unresolved edges and zero
  overlap pairs in this small preparation sample. No labels or synthetic replication
  were included. These are the first five source records per config, not the frozen
  pilot selections. HybridQA was not tested.
- Independently recomputed the join hash, counts, edge resolution and overlap from
  the saved JSONL inputs without rerunning Spark or rewriting artifacts. They match
  both `python_reference.json` and `spark_measurement.json`; canonical joined hash:
  `c06a3ec4544dea233c95346ccc4776af17d1510b4b494a3601a9a15fdb13d791`.
  Parquet `_SUCCESS` markers exist for facts, documents and questions; Spark event
  logs are retained. Spark's saved wall time is 8.128820 seconds.
- `resources_localfs.json` records the successful invocation: exit 0, 8.996029
  seconds including the wrapper's measured process lifetime, peak sampled process-tree
  RSS 835,276,800 bytes (796.58 MiB), four processes, 0.1-second sampling.
  `resources.json` is an earlier failed invocation (exit 1, 5.666788 seconds,
  647,938,048 bytes); retain it as failure evidence, not as the successful resource
  result. The JSON resource records do not establish the failure cause or the retry's
  environment settings. Summed RSS may double-count shared pages and miss short peaks.
  This is single-machine correctness acceptance, not a distributed-cluster result,
  speedup claim or repeated cold/warm benchmark.

`artifacts/overlap_dev_v3.json` covers all available dev records from five datasets:
FinQA 883, TAT-QA 1,668, ConvFinQA 1,490 turns, TAT-HQA 824 and MultiHiertt 1,044
(5,909 total); `limit_per_source=null`. All five recorded config hashes still match.
The artifact records `labels_used=false` and `official_splits_changed=false`.
The audit script defines the exact categories as follows:

- **Source:** equal `document.filename`, falling back to `document.id`; this is
  identifier equality, not proof of byte-identical original reports.
- **Table:** equal SHA-256 fingerprints of the canonical reader-provided table
  payload (`table`, otherwise `tables`, otherwise `tables_html`). Representation
  differences can hide equivalent tables.
- **Question + table:** equal fingerprints of that table payload together with the
  question after trimming and lowercasing; internal whitespace is not normalized.
- **ID:** equal reader example IDs. Different dataset ID conventions can conceal
  shared evidence, so zero ID matches does not establish independence.
- **Content:** equal fingerprints of all reader fact texts joined in order with
  spaces. This is an exact reader-content check, not a raw report-file comparison.
- **Near:** eight deterministic MinHash minima propose cross-dataset document-key
  pairs; exact Jaccard similarity of lowercased word 5-gram sets must be at least
  0.8. Keys use dataset/split plus the reader's document ID. These can represent
  multiple FinQA question IDs or ConvFinQA Single/Double contexts from one source.

Exact counts below are **distinct shared keys per category and dataset pair**,
not numbers of overlapping questions. Near counts are **qualifying document-key
pairs**, so the columns have different units and must not be added together.
Categories can describe the same shared evidence.

| Dev dataset pair | Source | Table | Question + table | ID | Content | Near pairs >= 0.8 |
|---|---:|---:|---:|---:|---:|---:|
| FinQA / ConvFinQA | 218 | 218 | 2 | 0 | 218 | 1,413 |
| TAT-QA / TAT-HQA | 0 | 273 | 0 | 0 | 273 | 273 |
| FinQA / TAT-QA | 0 | 0 | 0 | 0 | 0 | 0 |
| FinQA / TAT-HQA | 0 | 0 | 0 | 0 | 0 | 0 |
| FinQA / MultiHiertt | 0 | 0 | 0 | 0 | 0 | 0 |
| TAT-QA / ConvFinQA | 0 | 0 | 0 | 0 | 0 | 0 |
| TAT-QA / MultiHiertt | 0 | 0 | 0 | 0 | 0 | 0 |
| ConvFinQA / TAT-HQA | 0 | 0 | 0 | 0 | 0 | 0 |
| ConvFinQA / MultiHiertt | 0 | 0 | 0 | 0 | 0 | 0 |
| TAT-HQA / MultiHiertt | 0 | 0 | 0 | 0 | 0 | 0 |

There are **21,585 candidate pairs checked, not 21,585 confirmed overlaps**.
Only **1,686** are in `near_duplicates` (1,413 + 273). Every retained pair has
Jaccard 1.0; there are no retained pairs with similarity in [0.8, 1.0).
Equal shingle sets do not by themselves prove identical full text, ordering or
questions. `candidate_cap_reached=false`; approximate candidate recall still means
this was not an exhaustive all-pairs search.

Representative input examples, without reference answers:

- Exact question + table: FinQA `STZ/2006/page_68.pdf-1` and ConvFinQA
  `Double_STZ/2006/page_68.pdf_0` both ask “what is the current ratio of robert
  mondavi?” and share source `STZ/2006/page_68.pdf`.
- The other exact question + table key: FinQA `GPN/2017/page_77.pdf-2` and
  ConvFinQA `Double_GPN/2017/page_77.pdf_1`, “what portion of the total purchase
  consideration is allocated to goodwill?” Both examples were checked directly
  through the current readers.
- Near report entries: `convfinqa:dev:finqa:dev:Double_AAP/2011/page_28.pdf`
  pairs separately with `finqa:dev:finqa:dev:AAP/2011/page_28.pdf-1` and
  `finqa:dev:finqa:dev:AAP/2011/page_28.pdf-2`, both at Jaccard 1.0. This shows
  why near-pair totals exceed distinct source/table totals.
- Across the TAT family, `tathqa:dev:003755794bbbbcffd0667b9600aeb0be` pairs
  with `tatqa:dev:13bb283b-4b9c-42b9-9b02-f1b2e1a87abf` at Jaccard 1.0,
  despite no exact cross-dataset example-ID matches.

Scoring implications: preserve official per-dataset splits, examples, denominators
and evaluators. Shared evidence does not invalidate a dataset's own score, but
related datasets do not provide independent replications. FinQA/ConvFinQA share
reports and tables; TAT-HQA often changes the task while retaining TAT-QA context,
so matching evidence is not automatically an identical question. Keep all dataset
scores separate and clearly label any combined summary and weighting; their official
metrics also differ. A pooled question-level score or ordinary independent-sample
confidence interval would overcount shared sources. Within-dataset uncertainty
should respect documents/conversations; any cross-dataset uncertainty needs explicit
shared-source clustering, which this artifact does not construct. Any future
overlap-filtered sensitivity analysis must be separately specified and reported
alongside official scores, with a new version if experiment inputs change.
No examples were removed and no frozen experiments were changed.

Limitations: this is an input-only **dev/dev** audit. It does not check train/test
or other cross-split contamination, hidden-test overlap, model pretraining exposure,
answer leakage or model accuracy. HybridQA is absent because its evidence corpus
is missing. Zero observed MultiHiertt or other cross-family matches is not proof of
disjoint underlying reports. Exact checks depend on reader representations and
identifier conventions; the near check uses sets (losing word frequency/order
beyond each 5-gram), an approximate candidate search and a fixed threshold.
No raw source hashes or audit-code hash are embedded in this overlap artifact;
its config hashes alone do not certify unchanged raw inputs since audit creation.
The full-dev overlap counts and the small Spark sample's zero overlaps describe
different scopes and must not be substituted for one another.

Next live-smoke command, from `/home/p_2626/BigDataEndSem/final`:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/p_2626/bigdata-env/bin/python -m nrqa.experiment run experiments/frozen_v3/smoke.json artifacts/live_smoke_v3 --mode live
```

Rechecked the active contract digest, current code hashes, raw source hash, three
selected input hashes and configuration equality without constructing a provider
or calling inference APIs. Contract remains
`fd6d6278330dcd28dabee59f1f4f9b005b5437b5ae9212ac54f909d173284974`:
Gemini `gemini-2.5-flash`, three explicit questions × three methods = nine logical
predictions, maximum 27 generation attempts, $0 spending ceiling. The live output
directory does not yet exist and is separate from prepare/mock/historical outputs.
This command is provided for later execution and was **not run**. Its documented
prerequisites remain valid free-tier/model/quota access and a current UTC-day
attestation in private `.env`; no secrets were read or printed during this update.
