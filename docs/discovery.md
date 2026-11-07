# Verified discovery

Inspection date: 2026-11-06. This is a read-only audit of reference materials plus planning-document updates. No installation, training, inference, dataset extraction, implementation execution, evaluator execution or report compilation occurred. Hardware probes, metadata/count/schema inspection and input-only overlap comparisons were performed. Test-bearing files were inspected for schema/counts/identifiers, not answer values.

## Instructions and requirements

The actual instructions file is `../final/Agents.md` (capital A, otherwise lowercase), not `AGENTS.md`. It requires planning-only work, six datasets, a shared core where justified, leakage prevention, and leaving parent repositories untouched. Read it before designing. Also read every current document. `docs/brief.md` is populated; `README.md`, `docs/spec.md`, `docs/audit.md`, `docs/plan.md`, and `docs/state.md` were empty at the start. The requested discovery/research/proposal paths did not yet exist; those are now created at the requested canonical paths, not competing versions.

The brief contains an older “all four datasets” sentence. The updated Agents.md and current user request explicitly require six and take precedence. The brief's relative deadline “tomorrow” is superseded by the user's clarification: **submission date 8 November 2026**, time of day unspecified. The user also confirms Spark/Hadoop are optional, useful if workload size warrants them. The brief describes a Windows laptop with 64 GB RAM / RTX 4060 8 GB; physical host configuration and exact API model/account limits remain unverified. The user subsequently confirmed a $0 budget with multiple free providers and quota-driven switching.

Verified deliverable: final report using `../Current_implementation/Chiru-End-Sem/acl2023`. Its TEX/STY/PDF and adjacent DOCX are generic ACL 2023 instructions, not a course rubric. Style specifies A4, two columns, 2.5 cm margins; source uses 11-point article. ACL conference page limits (8/4), mandatory Limitations and encouraged Ethics are template rules, not established course requirements. Include limitations for research quality regardless. Old implementation-plan suggestions of 8–12 pages, ten notebooks or presentation format are not verified requirements. Deadline time, page limit, grading weights and demo/notebook needs remain unknown. Spark and Hadoop are not mandatory, per the user's clarification.

Template issue: `acl2023.tex:8` requests uppercase `ACL2023`, but the local style is `acl2023.sty`. This is a likely case-sensitive compilation problem; test later on a copy inside `final/report/`, leaving the original intact. Do not inherit placeholder authors, sample citations or anonymous review mode without checking the required final format.

## Repository identity and contents

Origins and HEADs read locally; no fetch performed. Sizes include `.git` and are rounded `du -sh` measurements.

| Directory | Origin | HEAD | Size |
|---|---|---|---|
| `../FinQA` | [czyssrs/FinQA](https://github.com/czyssrs/FinQA) | `0f16e2867befa6840783e58be38c9efb9229d742` | 142 MB |
| `../TAT-QA` | [NExTplusplus/TAT-QA](https://github.com/NExTplusplus/TAT-QA) | `870accc41953dcde885aabeb963d94aabdc0fbc3` | 41 MB |
| `../ConvFinQA` | [czyssrs/ConvFinQA](https://github.com/czyssrs/ConvFinQA) | `cf3eed2d5984960bf06bb8145bcea5e80b0222a6` | 36 MB |
| `../HybridQA` | [wenhuchen/HybridQA](https://github.com/wenhuchen/HybridQA) | `db22fda8c5951438fade3c69d75b350335ba93b3` | 103 MB |
| `../TAT-HQA` | [NExTplusplus/TAT-HQA](https://github.com/NExTplusplus/TAT-HQA) | `8b821d89f0fbfeceea07e4f5faf46b33150fee07` | 69 MB |
| `../MultiHiertt` | [psunlpgroup/MultiHiertt](https://github.com/psunlpgroup/MultiHiertt) | `45bd9ccdf3142ea059bd5e69c0afb83437fa539c` | 524 KB |

No `.pt/.pth/.bin/.ckpt/.safetensors/.pkl/.pickle` model artifacts were found in the six repositories. Bytecode caches are not model checkpoints. Original papers were read online through primary sources linked in research.md; do not assume PDFs or checkpoints are bundled locally. README download links do not establish successful download or current service availability.

### Exact split availability

| Dataset / local file | Contexts or conversations | Questions/turns | Labels and caveats |
|---|---:|---:|---|
| FinQA `dataset/train.json` | — | 6,251 | Labeled |
| FinQA `dataset/dev.json` | — | 883 | Labeled |
| FinQA `dataset/test.json` | — | 1,147 | Public labeled test; quarantine labels |
| FinQA `dataset/private_test.json` | — | 919 | Question-only QA field; overlaps public test |
| TAT-QA `dataset_raw/tatqa_dataset_train.json` | 2,201 | 13,215 | Labeled |
| TAT-QA raw dev | 278 | 1,668 | Labeled; use this for dev evaluation |
| TAT-QA raw test | 278 | 1,669 | Unlabeled |
| TAT-QA raw `tatqa_dataset_test_gold.json` | 277 | 1,663 | Separate released gold version; entirely different UIDs from public test |
| ConvFinQA ZIP `data/train.json` | 3,037 | 11,104 | Labeled conversation file |
| ConvFinQA ZIP `data/dev.json` | 421 | 1,490 | Labeled conversation file |
| ConvFinQA ZIP `data/test_private.json` | 434 | 1,521 | Hidden labels |
| HybridQA `released_data/train.json` | table IDs only | 62,682 | Questions/answers; corpus absent |
| HybridQA `released_data/dev.json` | table IDs only | 3,466 | Questions/answers; corpus absent |
| HybridQA `released_data/test.json` | table IDs only | 3,463 | Unlabeled |
| TAT-HQA raw `tatqa_and_hqa_dataset_train.json` | 2,207 | 19,878 mixed | 13,251 factual + 6,627 hypothetical |
| TAT-HQA raw dev | 274 | 2,468 mixed | 1,644 factual + 824 hypothetical |
| TAT-HQA `dataset_test_hqa/tathqa_dataset_dev.json` | 277 | 832 | **Hidden test**, despite filename |
| MultiHiertt | unavailable | unavailable | Code only; published total 10,440 is not a local count |

FinQA also includes `code/evaluate/test.json` (1,147) and example predictions (1,050): examples are not complete evaluation output. Labeled QA fields include `program`, `gold_inds`, `exe_ans`, `program_re`, explanation, annotation rows, cached retrieval and `model_input`. Use only raw text/table plus `qa.question` for inference; cached evidence fields are not safe by default. Keep both `table` and `table_ori` for source fidelity and evaluator compatibility.

ConvFinQA `data.zip` is 17,512,756 bytes, with six JSON members and a directory member. It also contains `train_turn.json` (11,104), `dev_turn.json` (1,490), `test_turn_private.json` (1,521). Expanded JSON total is about 249 MB; conversation files avoid repeating document payload per turn. Archive inspected in memory, not extracted. Private turn annotation contains `cur_dial` only; do not depend on labeled `turn_ind` or `dialogue_break` being available there.

TAT-QA `dataset_tagop` contains train (13,215) with derived `facts/mapping`, and dev (1,668) **without labels**. `sample_prediction.json` is an example prediction map. TAT-QA public test vs test-gold: zero shared question UIDs and table UIDs; never zip/join by position. For final local testing, use the test-gold release's own input-only view and its own IDs, label it “released test-gold version, 1,663 questions.” If comparability to the original 1,669-question benchmark is required, a verified release mapping is a separate unresolved requirement; do not infer it from row order.

TAT-HQA has nine JSON data files: two mixed raw; two mixed processed under `dataset_extra_field`; factual processed `orig/` train/dev; hypothetical processed `counter/` train/dev; hidden test. Processed mixed files live directly under `dataset_extra_field`, not a `both/` directory. The raw hypothetical answer type is `counterfactual`; processed files instead carry a `counterfactual` flag and ordinary answer type. Hypothetical train/dev categories: arithmetic 5,553/707; span 621/58; multi-span 148/27; count 305/32. Evaluate the hypothetical dev set using `dataset_extra_field/counter/tatqa_and_hqa_field_dev.json`, keeping its label-derived fields entirely outside inference. It is **hypothetical QA**, not a hierarchical-table dataset. Raw actual key `rel_paragraphs` differs from README spelling. Answer values are heterogeneous, not always lists.

HybridQA traced train/dev files repeat the question counts and add weak-supervision `answer-node` labels. `dev_reference.json` has 3,466 references and table/passage groups of 1,349/2,025; these groups do not exhaust all questions (92 remain outside them). `test_answers.json` has 3,463 pipeline-shaped records with `pred`, `nodes`, `target`; it is not verified test gold. Required `WikiTables-WithLinks/tables_tok` and `request_tok` are absent across the parent workspace. [Official linked-corpus description](https://raw.githubusercontent.com/wenhuchen/WikiTables-WithLinks/master/README.md) confirms cell text + hyperlink lists and table ID mapping. Acquire the correct version later and verify every referenced table/link resolves; traced answer locations are not replacement evidence.

MultiHiertt has 44 non-Git files, no JSON, no `dataset/` and no checkpoints. README and code expect `uid`, paragraphs, HTML tables, cell-keyed `table_description`, and `qa` containing question/answer/program/text_evidence/table_evidence. Preserve its string cell IDs and HTML hierarchy. Actual data schema examples and split counts remain unverified until acquisition. Author README links [Google Drive data](https://drive.google.com/drive/folders/1ituEWZ5F7G9T9AZ0kzZZLrHNhRigHCZJ) and [Hugging Face artifacts](https://huggingface.co/datasets/yilunzhao/MultiHiertt/tree/main). The latter web view did not expose a usable file listing; do not claim data download is confirmed. Existing fetch script was read, not run.

## Compatibility comparison

| Dataset | Prediction-time structure | Reasoning/answers | Training-only annotations and special handling |
|---|---|---|---|
| FinQA | Financial report excerpt: pre/post text + one table | Composed arithmetic, comparison, table aggregates; mostly numeric, comparison outputs possible | Programs and evidence; exact official DSL constants/operators and table row semantics matter |
| TAT-QA | One table + ordered paragraphs, current question | Span, multi-span, count, arithmetic, comparison/sorting; predicted scale | Derivation, answer type/source, scale, evidence mappings excluded; preserve nested/implicit headers where present |
| ConvFinQA | FinQA-like context + question prefix through current turn | Number selection, multi-step arithmetic with conversation references | Gold turn programs, answers and original source questions excluded; evaluate full ordered conversations |
| HybridQA | Assigned Wikipedia table + passages linked from cells | Entity/span retrieval and multi-hop table/text reasoning; not restricted to arithmetic | Answer text and traced answer-node excluded; retain link targets and table identity |
| TAT-HQA | TAT-QA-like context + explicit hypothetical clause | Change a fact then arithmetic/count/span/multi-span; scale | Related factual question/answer and intervention labels excluded; parse assumption from question itself |
| MultiHiertt | Multiple HTML tables with hierarchy + longer text | Cross-table reasoning, arithmetic programs or spans | Gold cell/text evidence and programs excluded; table descriptions must be established input-derived or regenerated without labels |

## Evaluator contracts and hazards

| Dataset | Official tool / output | Metrics and necessary wrapper behavior |
|---|---|---|
| FinQA | `code/evaluate/evaluate.py`; list `{id, predicted:[tokens..., "EOF"]}` | Execution accuracy (rounded result) and symbolic program equivalence. Script denominator is prediction count; preflight exact expected ID coverage. |
| ConvFinQA | Submission: list `{id,predicted:[tokens...,"EOF"]}`. Local `code/utils/general_utils.py::evaluate_result` expects n-best dict, candidate `id,pred_prog,ref_prog` | Execution/program accuracy. Trusted evaluator alone attaches `ref_prog`; never trust model-supplied references. Check full denominator. Hidden test needs external scoring. |
| TAT-QA | `tatqa_eval.py` + `tatqa_metric.py`; UID → `[answer, scale]` | EM/F1/scale. Honor normalization; numeric scalar zero is falsey in metric path, so serialize numeric answers as strings (or valid lists for multi-span), verified by fixtures. Use exact release's UIDs. |
| HybridQA | `evaluate_script.py`; list `{question_id,pred}` + reference object | Normalized text EM/token F1 overall and subgroups. Missing IDs may crash, duplicates overwrite; enforce coverage and uniqueness first. Hidden test submission service availability unverified. |
| TAT-HQA | Root `evaluate.py`; UID → `[answer,scale]` | EM/F1, scale tracked internally; arithmetic/count F1 equals EM. `judge()` calls undefined `qcnt` at line 517; helper is `qcount`. Later wrapper can call unchanged `evaluate_json` directly or document a minimal CLI-only patch in final, never edit upstream. Numeric-zero caveat also applies. |
| MultiHiertt | `evaluate.py`; list `{uid,predicted_ans,predicted_program}` assembled from span/program files | Combined EM/F1, not standard program accuracy. Program equality after execution, normalized span metrics, custom mixed-type tolerance. Missing IDs crash; CLI reconstructs dataset path. Test asks for external scoring. |

Metric caveats must be tested before calls: FinQA/MultiHiertt execution rounds final numeric results to five decimals; TAT normalization handles scale and percent, so README scale wording is not a replacement for code behavior. MultiHiertt program/program evaluator overwrites predicted invalid flag with gold invalid flag; prevalidate output and score invalid cases as failures rather than exploiting the bug. Preserve an unmodified official-score run and disclose any corrected diagnostic metric separately. None of these evaluators was executed in this planning phase.

## Measured overlap, and limits of the check

Read-only aggregate checks used source IDs/filenames and exact input table grids plus question strings. They are preliminary, not a full near-duplicate audit. Test identifiers only were compared; no test question/answer inspection informed the proposal.

| TAT-QA split → TAT-HQA factual split | Identical unique table grids | Identical unique table-grid + question pairs |
|---|---:|---:|
| Train → train | 2,181 | 13,016 |
| Train → dev | 0 | 0 |
| Dev → train | **3** | **9** |
| Dev → dev | 273 | 1,624 |

All checked cross-repository TAT question UIDs differ, so UID-only auditing misses this overlap. TAT-QA test-gold and TAT-HQA hidden test share 277 table UIDs. Mixed TAT-HQA facts are not independent extra training examples. Main no-training/zero-shot design avoids intentionally learning these labels, but shared contexts still invalidate treating datasets as independent samples.

FinQA↔ConvFinQA shared source filenames: train/train 1,588; dev/dev 218; public test/private conversation test 260; FinQA private test/private conversation test 227. Other cross-split pairings have zero exact filename overlap. Removing `Single_` from ConvFinQA IDs maps all 2,109 train, 300 dev and 306 private-test single-source conversations to FinQA IDs in the corresponding train/dev/public-test splits. Double-source counts are 928/121/128; their source question mapping requires more than prefix removal. FinQA public/private test themselves share 726 IDs and 303 filenames. Do not count them as independent test data.

Within checked ConvFinQA train/dev/private test, conversation IDs and filenames are disjoint. In labeled turns, `cur_dial` equals the prefix through current turn in 11,104/11,104 train and 1,490/1,490 dev records. Full annotations expose future questions in 8,067 train and 1,069 dev turns and contain gold answer lists throughout. The official generator uses joined `cur_dial`, not gold prior answers. These counts justify an explicit inference allowlist.

Still required: persistent file checksums and overlap artifacts, partial/near-duplicate report detection, cross-family checks after missing data acquisition, and review of any approximate evidence annotations. The earlier prototype's claim of 12 overlaps is based on different units/logic and is not interchangeable with the 9 exact question+table matches above.

Source-family overlap matters beyond the measured pairs: [FinQA](https://aclanthology.org/2021.emnlp-main.300/) uses 1999–2019 S&P 500 reports collected in FinTabNet; [MultiHiertt](https://aclanthology.org/2022.acl-long.454/) also builds on FinTabNet and cites FinQA among its data sources. Their exact shared documents remain unmeasured because MultiHiertt data are absent. [TAT-QA](https://aclanthology.org/2021.acl-long.254/) draws from annualreports.com and reports 182 source reports; TAT-HQA extends it. Different repository names do not establish disjoint source companies/reports. HybridQA's Wikipedia origin is distinct, but exact/near-duplicate auditing should still cover every acquired input.

## Existing implementation audit

`../Current_implementation` is 43 MB. Its README lines 12–15 explicitly says ingestion is built while retrieval/reasoning/evaluation are unwritten. No saved predictions, metrics, build logs or built data were found to substantiate its reported 112 seconds, 9,832→5,576 documents, 384,827→220,884 blocks, or 12 flagged evaluation questions. These are **unverified reported preprocessing results**, not QA accuracy. Old plan accuracy targets (e.g. 65–70) and worked examples are illustrative, not measured.

Concrete static findings (paths relative to `../Current_implementation/Chiru-End-Sem`):

- `tests/test_adapters.py:34,55` checks only first 400 records/split and reference-ID resolution, not evidence correctness/completeness; skips cases without evidence.
- `src/finqa/ingest/tatqa.py:75,190` derives approximate evidence from label/derivation values; repeated numbers can mark unrelated cells. Do not treat this as official evidence gold.
- `src/finqa/normalize/programs.py:283` can replace failed derivation conversion with `span(gold_answer)`; nonempty-program coverage is not reasoning coverage. At line 218, inclusive comparisons become strict comparisons.
- `src/finqa/ingest/finqa.py:149–156` stores prior gold programs/answers in ConvFinQA history; feeding it wholesale would be oracle history. No completed leaked inference run is demonstrated. Private turn handling also loses history when expected labeled fields are absent.
- `src/finqa/normalize/consolidate.py:97,102` deduplicates by question ID before flagging overlap and retains flagged questions. Exact normalized document hashing misses partial and near duplicates; evaluation filtering must remain a separate reported subset.
- `src/finqa/ingest/run_ingest.py:51,132` discards parse-error records without a complete error denominator. Require manifest counts and explicit failures instead.
- Registry has no HybridQA reader. No official evaluation wrapper is implemented. The old MultiHiertt metric plan does not match its combined EM/F1 evaluator.

Reuse policy: inspect small number/table utilities as reference, but require fresh semantic checks and a prediction/reference separation before copying anything. Do not run old fetch scripts or build commands as part of planning. Parent sources remain read-only.

## Measured environment

| Probe | Observed result |
|---|---|
| OS | WSL2 kernel `6.6.87.2-microsoft-standard-WSL2`, Microsoft hypervisor |
| CPU | Intel Core i7-14650HX; guest exposes 8 logical CPUs, 4 cores × 2 threads. Not a claim about full physical host topology. |
| RAM | `free -h`: 47 GiB total, ~45 GiB available, 16 GiB swap unused at inspection |
| Disk | `/dev/sdd`: 1007 GiB virtual filesystem, 35 GiB used, 922 GiB available. Windows backing-drive free space unknown. |
| GPU | `nvidia-smi`: OS blocks NVML. Torch CUDA build 13.0; `cuda.is_available()` false, count 0. GPU model/VRAM not verified from session. |
| Python | Existing `/home/p_2626/bigdata-env`, 6.4 GB; Python 3.12.3 |
| Installed metadata | torch 2.13.0, PySpark 4.2.0, pandas 2.3.3, PyArrow 25.0.1, NumPy 2.5.2; SciPy 1.18.0, SymPy 1.14.0, scikit-learn 1.9.0, tqdm 4.70.0, BeautifulSoup 4.15.0 |
| Missing metadata | transformers, accelerate, bitsandbytes, llama-cpp-python, vllm, pytest, lxml |
| Java/Hadoop | OpenJDK 21.0.12.1; Hadoop executable at `/home/p_2626/hadoop/bin/hadoop`, version 3.3.6 |
| Model cache | No suitable text model identified; inspected Hugging Face listing shows only an unrelated timm model cache |

Package metadata is not proof Spark jobs, old evaluators or GPU inference run successfully together. Spark/HDFS services were not started. No compatibility claim is made for historical torch 1.x/transformers environments. Common cgroup limit paths were absent; visible memory/CPU probes are not a guarantee of sustained allocation. Hardware/resource estimates are in proposal.md and must be benchmarked during implementation.

`pdflatex` was not found on the current PATH; report compilation availability is another implementation-phase check, not a reason to install anything in planning. `git status` in final reports that it is not a Git repository, despite the managed `.git` directory; do not claim a Git diff/commit exists for these planning updates.


## API availability follow-up, 2026-11-06

User supplies candidate providers Gemini, OpenAI, OpenRouter, Groq and Mistral and authorizes a **free-only, $0** plan with switching on quota exhaustion. This confirms a preference, not usable quotas or exact free model access. No account/credential inspection or inference occurred.

Official sources reviewed: [OpenAI pricing](https://developers.openai.com/api/docs/pricing) and [rate limits](https://developers.openai.com/api/docs/guides/rate-limits), [OpenRouter limits](https://openrouter.ai/docs/api_reference/limits), [Groq limits](https://console.groq.com/docs/rate-limits), [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing?hl=en) and [limits](https://ai.google.dev/gemini-api/docs/rate-limits?authuser=2). They distinguish model/account-specific eligibility and request/token limits; do not infer free access from a low-price model or a usage-tier name. Gemini limits can apply to a project rather than an individual key. Exact limits must be recorded from the actual accounts at setup. Mistral's earlier tier URL returned 404; current [usage/limits documentation](https://docs.mistral.ai/admin/billing-usage/usage-limits) was located in official search, but account-specific API eligibility remains unverified. Search retrieval of Gemini pages had a content-type failure before alternate official search results were available. None of these checks establishes sufficient free capacity for all planned runs.
