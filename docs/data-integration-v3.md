# Real-data integration audit, version 3

Inspected 2026-11-06. No inference APIs, packages, downloads or upstream/raw-data
changes were used. `AGENTS.md` is absent; the actual `Agents.md` was read.

## Locations and actual releases

`../HybridQA/released_data` contains `train.json`, `dev.json`, `test.json`,
`train.traced.json`, `dev.traced.json`, `dev_reference.json` and a README.
Use the plain question files. Traced `answer-node` fields are labels, not evidence.

| HybridQA split | Questions | Unique assigned tables | Duplicate question IDs | Prediction inputs validated | Blocked |
|---|---:|---:|---:|---:|---:|
| Train | 62,682 | 12,374 | 0 | 0 | 62,682 |
| Dev | 3,466 | 3,053 | 0 | 0 | 3,466 |
| Test | 3,463 | 3,061 | 0 | 0 | 3,463 |

Question records contain `question_id`, `question`, `table_id` and POS tags;
train/dev additionally contain `answer-text`. Dev reference IDs match all 3,466
question IDs and the answer strings match exactly. Test has no answer labels.
No real `tables_tok`, `request_tok`, WikiTables-WithLinks directory or relevant
archive was found in either supplied location or the parent project workspace.
The only tables_tok/request_tok directories found belong to synthetic fixtures.
The ConvFinQA ZIP and prior project delivery archive are not HybridQA corpora.

Every assigned table needs `tables_tok/TABLE_ID.json` and
`request_tok/TABLE_ID.json`. The first contains header/data cells with link lists;
the latter maps links to passage text. Without tables we cannot enumerate actual
passage targets. Validation reports exact missing filenames and affected question
IDs for **every** assigned table; it does not substitute traces or count zero links
as successful passage resolution.

`../MultiHiertt_data/multihiertt_data` contains three standalone JSON lists:

| Split | Records | Bytes | Labels | Duplicate IDs |
|---|---:|---:|---|---:|
| Train | 7,830 | 262,497,396 | 6,306 arithmetic + 1,524 span | 0 |
| Dev | 1,044 | 36,118,558 | 842 arithmetic + 202 span | 0 |
| Test | 1,566 | 52,242,696 | question only | 0 |

Actual keys are `uid`, `tables` (HTML strings), `paragraphs` (strings),
`table_description` (cell-ID map), and `qa`. Train/dev QA keys are question,
answer, program, table_evidence, text_evidence and question_type. Arithmetic
answers are floats and span answers are strings. Test QA contains only question.
The original file names and split membership are preserved.

## Reader corrections justified by these files

All inspected MultiHiertt HTML cells use `td`, including multi-row headers; no
`th` cells occur. The old fixture-oriented reader therefore lost second header
rows, section years and some unit labels. The new reader retains HTML and merged
geometry, infers the leading header block and later section headings from raw
content, and explicitly flags inferred structure as uncertain. It retains column
header chains, row labels, section units and year changes. The real GOLD/COPPER
section regression verifies that ounces and pounds do not form a dependency cycle
or carry the earlier unit into the later numeric section.

String evidence IDs use expanded grid coordinates. Eight train evidence references
address interiors of valid merged cells. The reader builds coordinate aliases from
rowspan/colspan alone and resolves them to the original cell anchor. It creates no
invented cells and reads no labels/descriptions to infer geometry or headers.
Original cell IDs, physical coordinates and HTML ordinal positions are preserved.

Every `## Table N ##` paragraph marker now links its corresponding table to the
ordered text. The adjacent preceding caption is retained as an explicitly uncertain
inference. All table markers resolve. Full audit totals below count context occurrences
per question, not independent unique documents:

| Split | HTML tables | Cells | Merged cells | Table/text links | Gold table refs | Gold text refs |
|---|---:|---:|---:|---:|---:|---:|
| Train | 31,567 | 1,809,803 | 40,168 | 31,567 | 19,762 | 6,582 |
| Dev | 4,050 | 250,536 | 5,023 | 4,050 | 2,683 | 932 |
| Test | 6,195 | 364,954 | 8,005 | 6,195 | hidden | hidden |

All 10,440 raw input records convert. All dependency edges resolve, no duplicate
fact IDs or dependency cycles remain, and every available gold evidence reference
resolves. Header/section/unit inference is still heuristic; structural validation
does not prove semantic correctness for every inferred header.

There are **61 unresolved cached description coordinates**: four entries in four
train questions and 57 entries in 12 test questions. Dev has none. They refer to
coordinates outside actual HTML cells, including generated `nan` entries. They
remain listed in `annotation_issues`; no cells/values were fabricated to match them.
This is a real metadata inconsistency. Our already-established input allowlist
excludes `table_description`, so these issues do not remove raw input records or
block QA answer scoring. A pipeline depending on those cached descriptions needs
its own reconciliation. We do not call the metadata completely clean.

Labels, programs, evidence annotations, question_type and cached descriptions stay
outside prediction inputs. Real train/dev examples of both answer types, and hidden
test examples, pass reference-mutation isolation checks. This tests the reader
boundary; it is not a claim to audit hosted-model pretraining contamination.

## Official output/scoring compatibility

The official program callback exports predicted_ans as a JSON number. Our old
adapter exported a numeric string, causing the unchanged mixed span/program scorer's
`math.isclose` call to fail. Program answers now use a numeric JSON value; span
answers remain strings. Official metric functions and tolerances are unchanged.
A real numeric-span regression tests that mixed branch.

All-ID abstention/export contract checks ran for train (7,830), dev (1,044), and
hidden test (1,566). Annotated splits also round-trip one arithmetic and one span
reference through the official scorer. These deliberately use references as test
expectations outside inference and are **not model predictions or QA accuracy**.
See `artifacts/data_integration_v3/scoring_contracts/summary.json`.

## Configurations, freezing and checks

MultiHiertt pilot/full-dev/full-test sources now point to the supplied relative
sibling directory. Config paths and explicit environment root overrides are
supported; no machine-specific absolute path was added to a source configuration.
HybridQA keeps its correct question paths and adds ordered configurable corpus
locations, with an explicit corpus override taking priority over auto discovery.
Missing or empty linked passages remain errors.

All 18 previous frozen files retain their exact bytes and hashes, compared with
the prior delivery archive. Versioned replacements live in `experiments/frozen_v3/`,
with three additional real-data MultiHiertt contracts (20-question pilot, full dev,
full test). Old IDs, model, seed, prompt and settings remain fixed for the 18 existing
experiments. `experiments/contracts_v3.json` records active versus historical files.
The delivery checker validates active code/input/contract hashes strictly and checks
historical file hashes without claiming old code contracts are currently runnable.
No HybridQA inference contract is fabricated while its corpus is missing.

Commands actually run:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/p_2626/bigdata-env/bin/python -m unittest discover -s tests -p test_real_data.py -v
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/p_2626/bigdata-env/bin/python -m unittest discover -s tests -v
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/p_2626/bigdata-env/bin/python scripts/validate_data_contracts.py
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/p_2626/bigdata-env/bin/python scripts/validate_local.py
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/p_2626/bigdata-env/bin/python scripts/check_delivery.py
```

Evidence: real_reader_tests.txt (6 tests), tests.txt (50 tests), scoring contracts,
frozen_replacements.json and the full local_validation.json with exact missing
HybridQA resources and description mismatch IDs. Live predictions, account access,
Spark execution and report compilation remain outside this validation.
