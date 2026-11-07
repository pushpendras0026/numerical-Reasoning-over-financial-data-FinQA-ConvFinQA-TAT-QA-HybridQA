# Verified data locations and remaining acquisition

Raw data and sibling repositories are read-only. New project files stay under
`final`. No downloads or installations were made for the version 3 audit.
See [data-integration-v3.md](data-integration-v3.md) for counts, schemas and caveats.

The default paths in JSON configurations are relative to `final`:

| Dataset | Development source | Final input option |
|---|---|---|
| FinQA | `../FinQA/dataset/dev.json` | `dataset/test.json`, 1,147 public labels |
| TAT-QA | `../TAT-QA/dataset_raw/tatqa_dataset_dev.json` | `tatqa_dataset_test_gold.json`, 1,663 own release IDs |
| ConvFinQA | `../ConvFinQA/data.zip`, `data/dev.json` | `data/test_private.json`, hidden labels |
| TAT-HQA | `../TAT-HQA/dataset_extra_field/counter/tatqa_and_hqa_field_dev.json` | `dataset_test_hqa/tathqa_dataset_dev.json`, hidden test |
| HybridQA | `../HybridQA/released_data/dev.json` | `released_data/test.json`, hidden labels; corpus still required |
| MultiHiertt | `../MultiHiertt_data/multihiertt_data/dev.json` | `test.json`, 1,566 hidden-label questions |

MultiHiertt train/dev/test are **present**: 7,830 / 1,044 / 1,566 records. Do not
redownload or move them. All raw inputs convert, and all annotated evidence resolves
through HTML geometry. There are 61 stale cached description coordinates (four train,
57 test), documented with exact IDs in the audit. Descriptions are excluded from
our prediction inputs; no values or cells are invented to repair this metadata.

HybridQA train/dev/test questions are **present**: 62,682 / 3,466 / 3,463. Its
`released_data` directory does not contain the linked evidence corpus. Traced files
and `dev_reference.json` are labels/reference metadata, not replacements for tables
or passages. All 69,611 questions currently lack their required corpus evidence.

The author's [README](https://github.com/wenhuchen/HybridQA#preprocess-data) points
to [WikiTables-WithLinks](https://github.com/wenhuchen/WikiTables-WithLinks).
To acquire it later in ordinary WSL, from `final`:

```bash
git clone https://github.com/wenhuchen/WikiTables-WithLinks data/WikiTables-WithLinks
```

Follow that repository's archive download/unpack instructions if needed. A clone
alone is not considered acquisition success: verify the actual files. Required
layout is `tables_tok/TABLE_ID.json` and `request_tok/TABLE_ID.json` for every
assigned table. Tables contain header/data cells `[text, links]`; request files map
link targets to nonempty text. Validation checks header and body links when files
are available. Empty or unresolved passages are explicit failures. Never substitute
`tests/fixtures/corpus` or answer-node traces to satisfy the check.

HybridQA configuration uses `corpus: "auto"` with these ordered candidates:

- `data/WikiTables-WithLinks`
- `../HybridQA/WikiTables-WithLinks`
- `../WikiTables-WithLinks`

A fixed `corpus` path may replace `auto`. These optional environment variables
allow alternate existing directories without editing code:

| Variable | Directory it selects |
|---|---|
| `NRQA_HYBRIDQA_QUESTIONS` | Directory containing HybridQA train/dev/test JSON files |
| `NRQA_HYBRIDQA_CORPUS` | Explicit root containing tables_tok and request_tok; overrides auto search |
| `NRQA_MULTIHIERTT_ROOT` | Directory containing MultiHiertt train/dev/test JSON files |

No override is needed for the supplied locations. An explicit invalid override
fails; it does not fall back silently. Changing locations or inputs after freezing
may change input hashes and requires a new versioned contract.

After acquiring HybridQA, run:

```bash
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python scripts/validate_local.py
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python -m nrqa.experiment freeze experiments/hybridqa_pilot.json experiments/frozen_v3/hybridqa_pilot.json
PYTHONPATH=src /home/p_2626/bigdata-env/bin/python scripts/check_delivery.py
```

A full list of currently blocked question IDs, missing table/request filenames,
source checksums and per-split readiness is saved in
`artifacts/implementation/local_validation.json`. Before a changed-code run, create
new versioned freezes and output directories; never overwrite prior contracts.
The current 21 runnable input/code contracts are under `experiments/frozen_v3`;
old contracts under `experiments/frozen` remain historical and hash-preserved.

Engineering fixtures are supplemental. Real-data readiness statements come from
full real split audits and scorer/export checks, not synthetic fixture success.
Do not tune on final test answers or join incompatible TAT-QA releases by position.
