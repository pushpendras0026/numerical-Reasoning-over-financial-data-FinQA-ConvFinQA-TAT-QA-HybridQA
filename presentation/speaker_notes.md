# Presentation script (15 minutes)

Part 1 is the video (`video/explainer.mp4`, 4:01), narrated live by one speaker.
Part 2 is the 10 slides (`slides.pdf`), about one minute each. Speaker A takes slides
1 to 5 and Speaker B takes slides 6 to 10. Swap the letters for names as you prefer.
Every number below comes from the measured results in the report.

## Part 1: video narration

| Scene | Starts | Say |
|---|---|---|
| Opening | 0:00 | (Title card: stay silent until the quote appears, about 6 s.) "A number in a financial report means nothing on its own. Our project is about what happens when a language model is given numbers without the labels that explain them." |
| What does 637 mean? | 0:22 | "This is a real FinQA table. The question asks for American Express's average payment volume per transaction. The answer is 637 divided by 5.0, but notice what makes that possible: the row label, and two column headers. Remove them and the model is left with two bare numbers. It cannot tell which is the volume and which is the count." |
| Reading budget | 0:52 | "In practice the model cannot read everything. A HybridQA document has a median of about 8,900 tokens, and we give the model a budget of fifteen hundred. So a system must decide which facts go in. Our question is whether the labels go in with them." |
| Pipeline | 1:16 | "Here is the pipeline, shared across all six datasets. A reader turns each dataset into facts, each one remembering which other facts explain it. BM25 ranks them, packing fills the budget, the model answers once, and its answer is checked and executed before the official scorer marks it. Packing is the only thing we change. Gold answers join only at scoring; we checked 443 saved prompts and none contained one." |
| Three packing methods | 1:50 | "Same budget, three ways to fill it. Ordinary packing repeats the labels inside every cell; that is a fair baseline, not a weakened one. Dependency packing follows each fact to its headers, units, hierarchy and links, and keeps each of them once, with the table structure. Length-matched packing adds neighbouring text up to the same length, to test whether more text alone is enough." |
| Literal grounding | 2:21 | "The model writes a small program and copies its numbers. Our code finds each number in the evidence. Both are there, so the program runs: 637 divided by 5.0 is 127.4. If a number appears nowhere, like 640 here, the answer is rejected. The earlier version asked for character positions instead and answered only 2 of 883 FinQA questions, though that run also used a different model." |
| Result | 2:58 | "And the main result. On all 3,466 HybridQA questions, dependency packing keeps more of the needed evidence at every budget. At 1,500 tokens, 146 questions are kept only by dependency packing and 7 only by ordinary. Across all six datasets, dependency packing is ahead at each dataset's chosen budget: about four points on HybridQA and MultiHiertt, under one point on FinQA and ConvFinQA. At the smallest budget, two hundred tokens, the extra structure costs coverage on ConvFinQA and MultiHiertt. And at four thousand tokens the gap is zero on the four smaller datasets." |
| Closing | 3:45 | "So: keep the labels with the facts, most of all when documents are much larger than the budget. Now let us show you how we tested this, and how far the answers follow." |

## Part 2: slides

**1. Title (A, 20 s).** Names. "We test whether keeping each number's labels with it helps when a model can only read part of a document."

**2. A number means nothing without its labels (A, 1 min).** Point to the two highlighted cells, then the row label and the headers. "The model needs all five. With a tight budget, labels compete with facts for space."

**3. Research question and data (A, 1 min).** Read the question in the box. "Same model, same budget; only packing changes. Four datasets were assigned and we added two. Related datasets share documents, so we never pool results. Feeding gold answers through each official scorer gives 100% on five datasets; MultiHiertt gives 90.5% because its span path drops minus signs."

**4. Pipeline (A, 1 min).** Walk left to right once. "Only the orange box changes. Labels stay apart until scoring. Every raw response is saved, so we can re-score without new calls. Spark builds the fact store."

**5. Three packing methods (A, 1 min 20 s).** Explain O, D and L in one sentence each. Then literal grounding: "copy values, code finds them, unknown values are rejected." Hand over to B.

**6. A fair experiment (B, 1 min).** "First fix: at 4,000 tokens four datasets were not truncated in a 40-question sample, so the comparison would have been empty. We chose budgets from document sizes without labels. Three measurements: coverage on all 9,268 questions with no model, then two answer blocks, each on a single model."

**7. Result 1, coverage (B, 1 min).** "Dependency is above ordinary on every dataset at the chosen budgets, most on HybridQA, 146 to 7, and MultiHiertt, 42 to 3. The gap closes as budgets grow, which is what the hypothesis predicts. Length-matched is lowest, so more text is not the same as the right labels."

**8. Result 2, answers (B, 1 min 20 s).** "On 50 paired questions per dataset, dependency is at least as good as ordinary on all six. The clear gain is TAT-QA, +11.3 points, with an interval from +4.1 to +19.9. MultiHiertt +9.8 and FinQA +2.0 just touch zero, and ConvFinQA is flat because its documents nearly fit. In Block B the executor does not reliably beat direct answering; direct wins on HybridQA, which has text answers and no arithmetic."

**9. What failed (B, 1 min).** "MultiHiertt first showed the executor 22 points ahead. Direct answers wrote percentages where gold uses fractions, and the official span path marks that wrong. Using one rule for both sides, the gap is +6.2 with an interval through zero, so we withdrew the claim. The remaining errors are real reasoning errors: wrong values, reversed percentage changes, over-long spans."

**10. Big Data and conclusions (B, 1 min).** "Spark builds a store of 1.36 million facts and 1.88 million dependency edges, with zero unresolved, and finds 491 pairs of identical documents across datasets, which is why we never pool. At this size Python is faster, 15.8 seconds against Spark's best of 37 at four cores, and we say so. Conclusion: keep labels with facts; it measurably preserves evidence, the answers move the same way, and only TAT-QA's gain is clear at this sample size." Invite questions.

## Likely questions

- *Why not a bigger sample?* Free-tier limit of 500 requests per day per model. Runs resume from saved answers, so more data only costs more days.
- *Is the comparison fair to ordinary packing?* It gets every label inline, at the same budget, model and prompt. Only the packing differs.
- *Why is Spark slower?* 1.4 million rows fit in one machine's memory; Spark's fixed start-up and coordination costs dominate. Its value here is a checked, partitioned store.
- *Could gold answers have leaked?* Labels are stored separately and joined only at scoring. A check of 443 saved prompts found no label fields.
