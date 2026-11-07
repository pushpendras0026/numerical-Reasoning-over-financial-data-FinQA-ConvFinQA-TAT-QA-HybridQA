# Research evidence and experimental design

Reviewed 2026-11-06. Sources below are primary papers and author repositories. Published numbers are context only, not results reproduced here. Local schemas, code and counts are documented separately in discovery.md.

## Original dataset sources

| Dataset | Original paper | Official repository / relevant method |
|---|---|---|
| FinQA | [Chen et al., EMNLP 2021](https://aclanthology.org/2021.emnlp-main.300/) | [czyssrs/FinQA](https://github.com/czyssrs/FinQA), FinQANet retriever + program generator. README corrects a label-leakage bug and reports corrected public-test execution/program accuracy 61.24/58.86 for RoBERTa-large. Use corrected code, not original inflated numbers. |
| TAT-QA | [Zhu et al., ACL 2021](https://aclanthology.org/2021.acl-long.254/) | [NExTplusplus/TAT-QA](https://github.com/NExTplusplus/TAT-QA), TAGOP tags evidence and applies operations; paper reports test F1 58.0. Test gold released in repository in January 2024. |
| ConvFinQA | [Chen et al., EMNLP 2022 / original paper](https://arxiv.org/abs/2210.03849) | [czyssrs/ConvFinQA](https://github.com/czyssrs/ConvFinQA). Paper Table 3: FinQANet RoBERTa-large 68.90 execution / 68.24 program accuracy; gold-evidence variant 77.32/76.46 is a different condition. GPT-3 program experiments use gold retrieval and are not direct end-to-end comparisons. |
| HybridQA | [Chen et al., Findings EMNLP 2020](https://arxiv.org/abs/2004.07347) | [wenhuchen/HybridQA](https://github.com/wenhuchen/HybridQA), HYBRIDER; official README test EM/F1 42.2/49.9 (base), 43.8/50.6 (large). Wikipedia linked text, not a finance-only or arithmetic-only dataset. |
| TAT-HQA | [Li et al., ACL 2022, Learning to Imagine](https://aclanthology.org/2022.acl-long.5/) | [NExTplusplus/TAT-HQA](https://github.com/NExTplusplus/TAT-HQA), L2I intervention over TAGOP. README checkpoint dev EM/F1 55.7/56.3 and test 55.6/56.3; these are author checkpoint reports. The hypothetical subset extends TAT-QA. |
| MultiHiertt | [Zhao et al., ACL 2022](https://aclanthology.org/2022.acl-long.454/) | [psunlpgroup/MultiHiertt](https://github.com/psunlpgroup/MultiHiertt), MT2Net retrieves facts, classifies answer type and selects spans or generates programs. Paper reports 10,440 questions over 2,513 documents and test F1 38.43. Local data missing. |

These baselines are relevant reference points, not a commitment to train six historical systems. Reproduction requires original checkpoint availability, compatible dependencies, identical split/input/history conditions, and verified evaluator behavior. Mark each report row `published`, `reproduced`, or `our controlled baseline`; never mix them in an improvement calculation.

## Closest work and the novelty boundary

| Verified work | Existing idea | Implication for this project |
|---|---|---|
| [Program of Thoughts, Chen et al.](https://arxiv.org/abs/2211.12588) and [PAL, Gao et al.](https://arxiv.org/abs/2211.10435) | Model-generated programs delegate calculation to an interpreter; PoT includes financial QA. | Executing arithmetic is established. Our ordinary retrieval + executable-plan baseline must already have this ability. |
| [TAT-LLM](https://arxiv.org/abs/2401.13223), [author implementation](https://github.com/fengbinzhu/TAT-LLM) | Extractor–reasoner–executor pipeline, instruction tuning and an external executor. | The broad architecture is not novel. We use one frozen model and isolate evidence packing instead of claiming a new reasoning pipeline. Its published inference setup is not a laptop feasibility measurement. |
| [EEDP / Evaluating LLMs' Mathematical Reasoning, ACL 2024](https://aclanthology.org/2024.findings-acl.231/) | Elicit, extract, decompose, predict; analyzes FinQA, TAT-QA, ConvFinQA and MultiHiertt, including table complexity and arithmetic steps. | Cross-dataset prompting/error analysis already exists. Reuse its failure categories as inspiration, but use official scorers rather than equating its manually interpreted answer assessment with official metrics. Project-site access failed during this review. |
| [FINDER, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1577/), [author code](https://github.com/subhendukhatuya/FINDER_POT_Financial_Numeric_Reasoning) | Generative retrieval plus program-of-thought reasoning with dynamically selected demonstrations, evaluated on FinQA/ConvFinQA. | Closest retrieve-and-execute system. Our retrieval is deterministic and main intervention preserves structural dependencies at a fixed token/call budget; dynamic demonstration selection is excluded. README and pipeline structure inspected; code not reproduced. |
| [FinCARDS, ACL Findings 2026](https://aclanthology.org/2026.findings-acl.1244/), [author code](https://github.com/XanderZhou2022/FINCARDS) | Structured financial evidence cards, entity/metric/period matching and tournament reranking with audit traces. | Closest evidence-selection mechanism. Finance-aware metadata and auditable retrieval are not novel. We test deterministic dependency closure of actual cells/headers/links and source-bound execution across varied inputs; no LLM card-generation or tournament stage. Inspected `pipeline/stage2_card_rerank.py`: API group filtering exists. This distinction is a proposed experimental focus, not proof of global novelty. |
| [Learning to Imagine](https://aclanthology.org/2022.acl-long.5/) and [MT2Net](https://aclanthology.org/2022.acl-long.454/) | Counterfactual fact intervention; retrieval with span/program reasoning over hierarchical tables. | Hypothetical overlays and answer-mode selection are required capabilities with clear predecessors, not separate novel contributions. |

Additional search found [T²-RAGBench](https://t2ragbench.demo.hcds.uni-hamburg.de/) and [FinLongDocQA](https://arxiv.org/abs/2604.03664), reinforcing that corpus/document retrieval must be evaluated separately from supplied-context QA. These are context for scope, not reproduced baselines. The search also returned [FinAgent-RAG](https://arxiv.org/abs/2605.05409); its primary arXiv page states it was withdrawn. Exclude its advertised gains from supporting evidence. Search results alone were not treated as verification.

Search scope: original dataset papers/repositories, executable financial QA, cross-dataset LLM studies, structure-aware evidence selection and recent financial RAG. This is a targeted literature review, not an exhaustive novelty search. No claim that nobody has used the exact proposed combination.

## Hypothesis, failure criterion and study boundaries

Mechanism: ordinary top-ranked chunks may contain a correct-looking number without its disambiguating year, ancestor header, unit or bridge link. Packing dependencies should increase interpretable evidence coverage and reduce wrong operands. It may instead crowd out relevant facts, propagate incorrect header inference, or add no value when full contexts fit.

Primary contrast is ordinary retrieval + executable reasoning versus the same system with dependency-preserving packing, at the same maximum evidence tokens, frozen model and one call/question. Report actual tokens as well as caps. The claim is not supported if answer-score differences are indistinguishable from zero or negative with useful confidence intervals, if wrong-operand errors do not decrease, or if a length-matched neighboring-context expansion explains the gain. Improvements only with more tokens/calls do not establish the fixed-budget hypothesis. Improvement on all six datasets is explicitly an unproven hypothesis.

Primary planned outcome: per-dataset official score, with FinQA/ConvFinQA execution accuracy and other datasets' F1; always publish companion official metrics. Report five-financial-dataset macro difference separately from HybridQA transfer. Do not treat six related datasets as independent replications. Cluster uncertainty by document/conversation and by known shared source when aggregating datasets. Avoid declaring a single blended score more important than per-dataset outcomes.

## Controlled experiments

| ID | Experiment | What it isolates |
|---|---|---|
| B0 | Ordinary row/sentence lexical packing + frozen model direct answer, same context cap | Simple shared baseline; shows whether the full system is worth its complexity. FinQA/ConvFinQA direct numeric accuracy is explicitly auxiliary: no invented programs/program scores. |
| B1 | Ordinary packing + shared typed plan + executor | Main strong control; official-compatible outputs. Shares retrieval features, headers in row text, model, demonstrations (initially zero), history and executor with P. |
| P | B1 + dependency-preserving packing | Main contribution. No extra model call. |
| A1 | P with dependency closure removed | Identical to B1; reuse cached results, do not pay for a duplicate ablation. |
| A2 | B1 + same-token neighboring rows/sentences instead of dependency-selected context | Tests whether gains are merely more surrounding text or longer input. Match actual token counts as closely as possible and report mismatch. |
| A3 | P with operand-source validation disabled, still execute numeric operations | Separates strict provenance enforcement from packing. Keep syntax validation; never run arbitrary generated code. |
| A4 | P without numeric execution, model supplies final numeric answer | Measures calculator contribution; direct-answer official program metrics unavailable and must be labeled. |
| D1 | On relevant subsets, remove ancestor headers / link expansion / predicted-history ledger / hypothetical overlay one at a time | Diagnoses which capability matters. These intentionally impaired systems are diagnostics, not equal-capability main baselines. |
| D2 | Gold-evidence oracle, labels supplied only in a separate diagnostic runner | Upper-bound evidence access; never include in main QA scores or call it deployable performance. |

Start with B1 versus P; add B0 and A2 before claiming a contribution. A3/A4/D1/D2 are lower priority if time or money is tight. A structured direct full-context baseline on contexts that fit is useful, but do not silently restrict the main denominator to these easy examples.

## Splits, overlap and conversations

1. Inventory all official split files and keep test labels separate. Inspect schema/counts without browsing test answer content. Select prompts, token budgets and operation policies using training/development only. Save development and final evaluation ID lists before calls.
2. Use a tiny training-fixture set for implementation debugging, then a fixed random development pilot. Sample whole ConvFinQA conversations, never isolated late turns. Report actual turn count. Reserve a development-confirmation partition by document before prompt tuning if test evaluation is unavailable; label it held-out development, not test.
3. Compare source document IDs, canonical text/table SHA-256 fingerprints, normalized question+context hashes, exact question IDs, and near-duplicate text (MinHash or token shingles) across all split/dataset pairs. FinQA↔ConvFinQA and TAT-QA↔TAT-HQA require special attention. Inspect near-duplicate candidates manually; no guessed overlap percentages.
4. Preserve official split scores. Additionally report overlap-filtered evaluation where feasible. Exclude overlapping target-evaluation documents/questions from any pooled training or few-shot bank. A corpus retrieval index may contain evaluation documents as unlabeled search targets; that is different from exposing their answers. Pretraining contamination of a hosted model cannot be fully audited; disclose it.
5. Evaluate ConvFinQA with predicted history, source-linked intermediate computations, and no future turns. Report turn index, full-conversation success, error propagation and questions-only history comparison. Gold-history results, if ever run, are separately labeled teacher-forced diagnostics.
6. TAT-HQA is not a conversation: related factual questions in the file are not assumed to be allowed history. Evaluate its hypothetical subset separately from the mixed TAT-QA records. Preserve official hidden-test identity even where its filename says `dev`.

## Metrics and evidence artifacts

Use exact evaluator revisions/output schemas in discovery.md. Report official EM (normalized exact match), token/span F1, execution accuracy, program accuracy and scale accuracy where applicable. Do not apply one tolerance/string comparison to all datasets. Before scoring, require exactly one prediction for every expected ID. Missing, malformed, timed-out and abstained outputs remain in the denominator. Report both coverage and accuracy; no success-only scores.

Per run save `manifest.json`, immutable split/ID list, input and dependency hashes, redacted requests, raw responses, parsed plans, evidence IDs, executor traces, official predictions, evaluator stdout/version, per-example scores and failure records. No secrets in artifacts. Compare unsupported DSL/format rate before interpreting answer quality; official program equivalence can disagree with correct alternative arithmetic.

Error labels: missing/wrong evidence; wrong table/row/year/entity; lost header/link; unit/scale/sign; operation/order; hypothetical target/change; conversation reference/propagation; invalid plan/execution; formatting/scorer mismatch. Analyze by dataset, answer type, arithmetic steps, hierarchy depth, evidence count, context length and turn. Gold labels can define analysis slices only after inference. For ambiguous causes, record multiple labels and have the student review a fixed sample of 20 disagreements/errors per dataset when available.

Resource evidence: preprocessing wall time, throughput, process-tree peak RAM, index size, Spark startup and spill, per-query retrieval/model/execution latency, p50/p95, input/output/billed reasoning tokens, cache hit rate, attempts and actual spend. Benchmark Python versus Spark `local[1]`/`local[4]` on identical source records with equivalent outputs; run three repetitions if practical. A replicated 10× input can measure processing scale but is labeled synthetic and creates no new QA evidence. Hadoop HDFS is optional unless the rubric requires it; local Parquet through Spark is the default. One laptop is not a distributed-cluster scalability result.

Use paired bootstrap intervals with at least 1,000 resamples by document/conversation for final comparisons, retaining paired predictions. Publish sample sizes and seeds. A 20-question pilot is a debugging signal, not evidence of broad superiority. If testing many ablations, mark them exploratory or correct multiple comparisons; focus the confirmatory claim on P versus B1.

## Report evidence map

| Report content | Required saved evidence |
|---|---|
| Problem and related work | This source ledger, explicit scope and novelty limits |
| Dataset section | Raw/source checksums, counts, missing-data status, overlap matrices and split manifests |
| Method | Schema, flow diagram, packer pseudocode, prompt, operation definitions, one trace without gold input |
| Main results | Frozen run manifests, paired official predictions, evaluator logs, CIs and failure denominators |
| Ablations/error analysis | Matched run IDs, actual token/call counts, error annotations and diagnostic labels |
| Big Data/system section | Spark/Python correctness comparison, time/RAM/storage/spill measurements; limitations of local execution |
| Reproducibility/limitations | Environment lock/snapshot, model revision/date, cost ledger, hidden-test restrictions, unavailable data and contamination caveat |

No numeric result belongs in the final report without an identifiable prediction artifact and scoring command, except a clearly cited published baseline.


## Free-provider scheduling amendment

User budget is now $0 with quota-driven switching among supplied providers. “Frozen model” means fixed within a comparison block, ideally the whole confirmatory subset. The controlled unit is example × all compared variants (whole conversation × variants for ConvFinQA). Complete all variants on one provider/model; checkpoint incomplete blocks and route fresh blocks elsewhere. Model changes never depend on answer correctness. Publish per-model paired results and quota attrition; any mixed-model aggregate is labeled a routing-policy result. Full scheduling and zero-spend controls are in proposal.md. No empirical result or free account quota is yet verified.
