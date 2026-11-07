# Implementation decisions and acceptance limits

Date: 2026-11-06. The saved proposal remains the design. These decisions resolve
concrete issues found during inspection; they do not use measured answer outcomes.

1. Retained FinQA, provider clients, durable ledger and existing semantic tests.
   Added a general experiment runner rather than expanding the fixed legacy smoke
   into six separate architectures. Its CLI is `python -m nrqa.experiment`.
2. Upgraded raw lexical overlap to deterministic BM25 using the same input-only
   candidates and direct dependency text for every packer. Header-only candidates
   remain accessible by closure/inline labels, not independent retrieved seeds.
   Their text is available for extraction once packed.
3. New prompts and schemas are necessary for spans, counts, aggregates, comparison,
   hypothetical changes and conversation state. Therefore use **new frozen files
   and new run directories**. Historical 404 artifacts and old prompts are retained
   as historical evidence, never silently resumed under a changed contract.
4. TAT table section rows and first-row/column headers are input-inferred and marked
   uncertain. MultiHiertt retains raw HTML and merged geometry. Descriptions are
   regenerated because upstream `table_description` provenance is not verified.
   Hybrid linked passages are split at sentence boundaries and depend on their
   originating cell, which depends on headers. No entire linked corpus is sent.
5. Packing accepts whole bundles only and never slices evidence strings. Baseline
   offsets refer to its actual inline-header strings. The dependency method closes
   recursively and deduplicates. C alternates ranked seeds with immediate source
   neighbors, fills to B's actual count, and logs the gap. This is an approximate
   length control with a different fact mix, not an exact causal isolation of length.
6. Offline counts use ceil(UTF-8 bytes/4) over stored facts including provenance.
   Provider counting charges the exact allowlisted evidence serialization, including
   its envelope, dependencies and location. User-text counts additionally include
   the question. Evidence caps exclude system/schema/question overhead, which is
   recorded separately through actual response usage. Mock counts are synthetic;
   a provider-backed counter interface does not make them real tokenizer evidence.
7. Current-question literals resolve only through `__question__`, an execution view
   of the exact prompt question. This is outside the evidence budget but inside
   recorded input length. Hypothetical amounts must lie within a question-grounded
   condition. Changes create a temporary numeric overlay; ordinary fact strings
   remain unchanged. Unknown units remain unknown. Operator correctness is still
   a model-reasoning question; span grounding cannot prove it.
8. ConvFinQA's reader uses the official `conversation_id_turn` convention, verified
   against all dev turn IDs. Each variant gets its own earlier predictions. Prior
   questions, predicted values and selected provenance consume evidence budget.
   Cumulative predicted programs are expanded with shifted intermediate indices.
   Future turns, original FinQA questions and gold answer/program lists are excluded.
   If a prior prediction is unavailable, it is not replaced with a gold value.
9. Answer tools reject bad shapes, duplicate JSON keys, unknown operations, invalid
   spans, partial numeric literals, unselected evidence, future steps, incompatible
   known units, division by zero, oversized values and unsupported exponent ranges.
   There is no generated-code interpreter. `exec` in `official_worker.py` loads only
   trusted local upstream evaluator definitions to bypass HybridQA's import-time
   command-line assertion; model output never reaches it.
10. FinQA/ConvFinQA use their unchanged official execution/symbolic functions.
    TAT-QA/TAT-HQA use the unchanged official metric classes. Calling these directly
    bypasses TAT-HQA's undefined CLI `qcnt`, without editing upstream. TAT numeric
    zero is serialized as text. HybridQA uses unchanged normalization/EM/F1 functions
    and reports table/passage subgroups where the reference file is available.
    Group scores use fractions internally; upstream CLI displays percentages.
    MultiHiertt uses its original program/span/mixed scoring functions. Its invalid
    predicted flag overwrite is disclosed: raw function outputs are saved and
    invalid pipeline outputs are separately forced to zero in the full denominator.
    Metric wrappers hash scorer and repository Python dependencies. They do not
    silently substitute a common tolerance or a generic exact-match score.
11. Complete selected table rows can use validated `table_sum`, `table_average`,
    `table_min` and `table_max` exports. Every numeric column and the exact row label
    must be selected; partial/repeated/mixed rows are rejected. General sums/means
    compile to arithmetic operations; min/max over arbitrary sets,
    extraction and some other valid local modes lack a supported FinQA program
    export. Such outputs are `unsupported_export` failures for official program
    scoring; no arbitrary identity program is generated. ConvFinQA supports the
    genuine single-number form. Direct-answer diagnostics disable execution and
    label FinQA/ConvFinQA numeric scores auxiliary; no program score is reported.
12. Run contracts freeze code, inputs, source hash, IDs, seed, prompt/schema, settings,
    provider and model before inference. Model metadata and resolved model stay
    pinned across variants/restarts. Every status stays in the scoring denominator.
    Scoring can describe a stopped partial run by explicit `missing` entries; that
    is not a completed paired experiment. Resumption replays from cached responses
    and reconstructs predicted histories in order.
13. Retained only existing Gemini and OpenAI. No free-pool scheduler was added:
    exact-model pairing and explicit quota stops satisfy this delivery boundary
    without adding unverified providers. Proposed A1 reuses ordinary results.
    Header/link/history/overlay removals and direct/no-executor diagnostics have
    configurations. Optional oracle-evidence and disabled-provenance studies are
    outside the confirmatory implementation: the current request requires validated
    source-bound operations, and oracle evidence would require a separate label-fed
    runner. They are not silently presented as completed experiments.
14. Spark has an implemented Python reference comparison, Parquet outputs and
    runtime/RSS commands. Actual equivalence is blocked at JVM startup here, so no
    runtime/resource/scalability claim is made. Near-duplicate candidate recall is
    approximate and pair-capped, with truncation reported. Repeated contexts are
    deduplicated by input content with original document/fact IDs retained as aliases,
    never called new QA examples. FinQA uncertainty clusters use source filenames,
    while conversation histories remain isolated to actual ConvFinQA conversations.
15. A source allowlist archive includes code/tests/docs/configs/report and redacted
    implementation evidence. Secrets, data, upstream repositories and provider
    ledgers are excluded. A local exact-secret scan precedes packaging. Git history
    cannot be certified because the managed directory is not a normal Git checkout.

Fixtures were authored/copied for engineering, including visible training labels.
No model generates their expected outputs. Passing scorers and mock replays proves
contract compatibility, not model accuracy or official benchmark reproduction.
