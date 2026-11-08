# Dependency-preserving evidence packing for numerical QA

With one model and a fixed evidence budget, does keeping each fact's headers, units,
hierarchy and links with it improve answers compared with ordinary packing? One
pipeline runs over FinQA, ConvFinQA, TAT-QA and HybridQA (assigned), plus TAT-HQA and
MultiHiertt (added). The report is [`report/main.pdf`](report/main.pdf).

## Pipeline

| Stage | Code | What it does |
|---|---|---|
| Readers | `src/nrqa/datasets.py`, `finqa.py` | Dataset to evidence facts with dependency edges; labels kept apart |
| Retrieval | `core.py: retrieve` | Deterministic BM25 over the supplied document |
| Packing | `core.py: pack_method` | Ordinary, dependency closure, or length-matched control |
| Answer plan | `grounded.py` | Model copies numbers and phrases; code resolves them to evidence |
| Execution | `execute.py` | Bounded decimal interpreter, official operations only |
| Scoring | `scoring.py`, `official_worker.py` | Official evaluators in isolated subprocesses |
| Run ledger | `runner.py`, `experiment.py` | Frozen contracts; saved raw responses; resumable runs |
| Big Data | `preparation.py` | Spark Parquet preparation, checked against a Python reference |
| Audit | `coverage.py` | Does gold evidence survive packing? Used after inference only |

## Results

All numbers are computed from saved outputs by `scripts/report_tables.py`
(`artifacts/v11/report_numbers.json`). Scores are official execution accuracy for
FinQA and ConvFinQA and official F1 otherwise; Block B uses a labelled relaxed numeric
measure for FinQA and ConvFinQA, whose direct answers have no program.

| Dataset | Coverage O / D (all dev) | Block A: O / D / L | D−O (95% CI) | Block B: executor / direct |
|---|---|---|---|---|
| FinQA | 96.3 / 97.3 (n=845) | 62.0 / 64.0 / 66.0 (n=50) | +2.0 (+0.0, +6.2) | 62.5 / 67.5 (n=40) |
| ConvFinQA | 97.1 / 97.4 (n=1,486) | 73.3 / 73.3 / 68.9 (n=45) | +0.0 (-6.0, +6.4) | 75.0 / 75.0 (n=36) |
| TAT-QA | 90.1 / 91.7 (n=1,636) | 60.2 / 71.5 / 69.4 (n=50) | +11.3 (+4.1, +19.9) | 65.2 / 58.7 (n=40) |
| TAT-HQA | 84.2 / 86.9 (n=792) | 56.7 / 60.7 / 52.7 (n=50) | +4.0 (-6.4, +14.5) | 60.0 / 56.7 (n=40) |
| HybridQA | 72.0 / 76.0 (n=3,466) | 54.9 / 60.1 / 49.8 (n=50) | +5.3 (-2.4, +13.0) | 50.2 / 66.6 (n=40) |
| MultiHiertt | 84.9 / 88.6 (n=1,043) | 47.0 / 56.8 / 41.0 (n=50) | +9.8 (+0.0, +20.0) | 63.7 / 41.7 (n=40) |

- **Coverage** (no model): D keeps more gold evidence than O on all six datasets at the
  chosen caps; the gap closes as budgets grow.
- **Block A** (`gemini-3.5-flash-lite`): D ≥ O on all six; the interval excludes zero
  only on TAT-QA.
- **Block B** (`gemini-3.1-flash-lite`): no consistent executor gain. Direct answering
  wins on HybridQA. MultiHiertt's +22.1 is a scoring artefact: under one rule for both
  sides it is +6.2 (−6.2, +20.0), see `scripts/multihiertt_sensitivity.py`.
- **Spark** (4.3.0): 1,360,644 facts and 1,884,748 edges, 0 unresolved,
  equal to the Python reference on every run. Python takes 15.8 s for the same
  work and Spark 37.0 s at best, so its value at this size is the checked
  Parquet store, not speed.
- **Tests**: 80 run, all pass, 1 skipped (MultiHiertt train is a Git LFS pointer):
  `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests`.

## Deliverables

| Deliverable | File |
|---|---|
| Report (6 pages) | [`report/main.pdf`](report/main.pdf), source `report/main.tex` |
| Slides (10) | [`presentation/slides.pdf`](presentation/slides.pdf), source `presentation/slides.tex` |
| Explainer video (4:01, 1080p) | [`presentation/video/explainer.mp4`](presentation/video/explainer.mp4), source `presentation/video/explainer.py` |
| Presentation script | [`presentation/speaker_notes.md`](presentation/speaker_notes.md): live video narration and slide notes |

## Setup

Needs Python 3.12, and Java 17 for Spark. Report builds use `tectonic`.

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
scripts/fetch_upstream.sh   # official evaluators, TAT-HQA, HybridQA linked corpus
printf 'GEMINI_API_KEY=...\nGEMINI_MODEL=gemini-3.5-flash-lite\n' > .env
```

## Reproduce

```bash
export PYTHONPATH=src
.venv/bin/python -m unittest discover -s tests         # no API calls
.venv/bin/python scripts/coverage_audit.py             # all dev questions, no API calls
scripts/run_v11.sh a gemini-3.5-flash-lite eval finqa tatqa tathqa convfinqa hybridqa multihiertt
scripts/run_v11.sh b gemini-3.1-flash-lite b_grounded,b_direct finqa tatqa tathqa convfinqa hybridqa multihiertt
scripts/run_spark.sh 100 1000 full
PYTHONPATH=src:scripts .venv/bin/python scripts/error_analysis.py artifacts/v11/b b_grounded dependency
PYTHONPATH=src:scripts .venv/bin/python scripts/report_tables.py
.venv/bin/python scripts/document_sizes.py             # median document sizes (video)
(cd report && make)                                    # report PDF, tectonic
(cd presentation/video && manim -qh explainer.py Explainer)   # times scenes from speaker_notes.md
```

Free-tier quota for `gemini-3.5-flash-lite` is 500 requests per day. Runs stop at the
limit and resume from their ledger, reusing every saved answer. `.env`, `artifacts/`
and `third_party/` are not tracked. OpenAI support exists in `openai_provider.py` but
was not used, because the available account has no credits.

## Layout

`src/nrqa/` pipeline; `scripts/` run and report tools; `tests/` unit tests;
`experiments/v11/` configs and `experiments/frozen_v11/` frozen contracts; `data/`
supplied datasets; `report/` LaTeX source and PDF; `docs/` brief, proposal and sources.
`docs/proposal.md` is the original plan: the answer format and caps changed since, and
the report describes the final design.
