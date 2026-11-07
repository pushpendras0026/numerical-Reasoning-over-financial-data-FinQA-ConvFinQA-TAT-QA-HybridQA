# Urgent recovery

The latest saved v5 runs contain 783 predictions. The recorded interpreter errors include 199 nonnumeric operands, 73 partial numeric literals, and 119 copied `exact supplied id` placeholders. Another 140 outputs have other invalid errors, 30 abstain, and 222 execute. Successful execution does not imply a correct answer. The single-operation restriction also excludes many valid solutions.

A new opt-in `answering: grounded` mode uses short evidence IDs and exact source quotes, deterministically resolves quotes to source spans, and sends the resolved plan through the existing interpreter. It restores up to 16 operations. Repeated quotes in a fact are rejected as ambiguous. This mode supports extraction and arithmetic; other answer types still require future work. It neither changes old predictions nor relaxes official scoring. No new model accuracy has been measured in the repair session.

Run in ordinary WSL:

```bash
cd /home/p_2626/BigDataEndSem/final
bash scripts/run_recovery.sh
```

The default freezes 10 development examples each from FinQA, TAT-QA and MultiHiertt, comparing direct answers under ordinary packing against grounded plans under ordinary and dependency packing. These compare answering strategies and are not a controlled estimate of the effect of packing across answering modes. Both grounded methods use the same inputs, schema, model and settings. FinQA necessarily overlaps the old full dev run; the other datasets exclude previous revised frozen selections. Complete conversations are preserved if ConvFinQA is requested.

It dispatches at most two local requests concurrently, stops new dispatch after 40 minutes, scores saved outputs with missing outputs retained, and adds the measured recovery table to the PDF. An active request may take up to the configured 180-second timeout beyond the dispatch deadline. Model weights/digest and prior settings are retained. Raw outputs, requests, ledgers, frozen contracts and metrics are in `artifacts/grounded_recovery_v1/`. Direct FinQA/ConvFinQA scores are auxiliary numeric accuracy, not official program scores. Failed connectivity exits before inference. No guaranteed positive score is claimed.

Optional smaller run (choose before the first launch; frozen files cannot change on resume):

```bash
bash scripts/run_recovery.sh --sample-size 5 --minutes 25
```

The repair session could not reach localhost:11434 or 172.25.80.1:11434. Windows PowerShell invocation also failed with a WSL socket error. This environment cannot perform the live run. The launcher must run where the existing local model is reachable.

The prior PDF, TeX source and complete historical revised table are preserved in `artifacts/grounded_recovery_v1/before_report/`. The current PDF summarizes the final measured revision, retains the original full-run/bounded results, and adds the measured root-cause counts. It is six pages instead of nine pages of repeated diagnostic tables.
