# Presentation script

Sixteen slides and twelve Manim visualizations (`video/clips/`, numbered in playing
order). Where a slide says **→ show**, stop on the slide, say "let's see how this works",
play the visualization and narrate it from the table below. Each visualization is timed
to its narration at about 140 words per minute. Speaker A takes slides 1 to 8 (problem
and method), Speaker B slides 9 to 16 (implementation, experiment, results).

## Crux video (4:32)

For a short talk, skip the individual **→ show** cues below and play `video/crux.mp4`
once, after **slide 9** (Dependency graph and packing). Say: "This is how the approach
works, from the problem, through the paper we started from, to our method on real data."
It joins four clips, narrated from the table below: A number needs its labels (0:00),
The reference pipeline (0:44), Our idea: a graph of labels (2:15), A real question,
replayed (3:33). Then continue with slide 10.

## Slide script

**1. Title (A).** "We study how to fit large financial tables into a language model's fixed context window without losing what the numbers mean."

**2. The task (A).** "This is an NLP task: answering numerical questions over financial reports. The model reads only what fits in its context window, so the system must choose which facts to pack, and how to write them." **→ show: The budget forces a choice.**

**3. The problem (A).** "A number means nothing without its labels. 637 and 647 differ only by their column header. Drop labels and numbers are ambiguous; repeat them in every cell and each cell costs four to eight times more." **→ show: A number needs its labels.**

**4. Prior approach (A).** "Arun and colleagues serialize tables into sentences that repeat the labels with every number, keep one chunk, and fine-tune T5 or Llama-2. Repeating labels is the cost we remove." **→ show: The reference pipeline.**

**5. Our contribution (A).** Read the boxed sentence, then the four items. **→ show: Our idea: a graph of labels.**

**6. Objectives (A).** "Each objective maps to the evidence on the right."

**7. Datasets (A).** "Four assigned datasets and two that stress hypotheticals and nested tables. Related datasets share documents, so we never pool."

**8. Pipeline (A).** "Only the packing step varies. Gold answers meet predictions only at scoring." Hand over to B.

**9. Dependency graph and packing (B).** "Ordinary repeats labels; dependency pays for each label once. The first cell costs more, every later cell less." **→ show: Paying for labels.**

**10. PySpark (B).** "Spark SQL explodes the dependency arrays into 1.88 million edges, checks that none is dangling, finds 491 duplicate documents and writes partitioned Parquet. At this size Python is faster; Spark gives a verified store." **→ show: Inside PySpark.**

**11. Grounded answers (B).** "The model copies numbers; code checks and computes. Invented numbers are rejected, wrong real ones are not, which is why labels matter." **→ show: Copy, then check.**

**12. Experimental setup (B).** "Three measurements, cheapest first. Answers come from Gemini 3.5 Flash-Lite, used as served with no fine-tuning; Block B uses Gemini 3.1 Flash-Lite." **→ show: How we measure.**

**13. Result 1 (B).** "Dependency keeps more gold evidence on all six datasets at the chosen budgets, 146 to 7 on HybridQA. The gap closes as budgets grow and reverses at 200 tokens." **→ show: Results.**

**14. Result 2 (B).** "Answers are at least as good on all six datasets and significantly better on TAT-QA, +11.3 points." **→ show: A real question, replayed.**

**15. Result 3 (B).** "The executor gives no consistent gain with this model. MultiHiertt's +22.1 was a scoring artefact; under one rule it is +6.2 with an interval through zero." **→ show: A result we withdrew.**

**16. Conclusion (B).** Read the five lines, then future work. **→ show: Conclusion.** Invite questions.

## Visualizations

| Clip | Slide | Say |
|---|---|---|
| The budget forces a choice | 2 | "A model is given a limited evidence budget, so a long report has to be cut. Here is the median document in each dataset, measured in tokens, against the budget we give it. A HybridQA document needs about 8,900 tokens, and the budget is 1,500. And the size depends on how labels are written. With labels repeated in every cell, the same documents grow, MultiHiertt from about 3,700 tokens to 6,400. TAT-QA's median document fits its budget of 400 only when each label is written once. So the question is not only which facts to keep, but how to pay for their labels." |
| A number needs its labels | 3 | "This is a real table from a Visa annual report, in the FinQA development set. The question asks for American Express's average payment volume per transaction. Our retriever ranks two cells highest: 637 and 647. Without their labels they are just two similar numbers. Only the column headers say that 637 is payments volume and 647 is total volume. So the answer, 637 divided by 5.0 billion transactions, which is 127.4, depends on the labels as much as on the values." |
| The reference pipeline | 4 | "Our starting point is a 2023 study, Numerical Reasoning for Financial Reports, by Arun and colleagues at Georgia Tech. It answers questions about an annual report in five steps. First it finds the tables in the PDF and extracts them. Then it serializes each table into sentences, such as: the revenue of 2019 is 100, the cost of 2019 is 50. It splits the text into chunks, and FAISS picks the one chunk most similar to the question. A fine-tuned model, T5 or Llama 2, writes the solution steps, and a regular expression parses them. Here is the crux. The fine-tuned T5 picks the right operation 95 percent of the time and the right numbers about two thirds of the time, but its own arithmetic is right only 12 percent of the time. Handing the arithmetic to a calculator lifts that to 62 percent. Three of its choices are where our project starts. Its sentences repeat the row and column label for every number. Its search keeps one chunk, so the model sees only part of the report. And its calculator lesson says the model should choose the numbers, and code should compute." |
| Our idea: a graph of labels | 5 | "Here is our idea, on the Visa table. Every cell becomes a fact, and every label becomes a fact too. Each number gets arrows to the labels it needs: its column header and its row label. The row label, American Express, is shared by every number in the row. Now a question arrives, and the retriever ranks 637 first. Packing takes 637 and follows its arrows, so payments volume and American Express come with it: 18 tokens. Next comes 647. It needs total volume and American Express, but American Express is already in, so only the new header is paid for: 29 tokens in total. 86 and 5.0 follow the same way, and the whole row costs 50 tokens. Each label enters once, and every number that needs it points to it. Ordinary packing would copy American Express next to every number instead, and the same row would cost 57. So the model receives a small table, inside the budget, where every number is still readable." |
| Paying for labels | 9 | "Here is the American Express row, packed two ways. Ordinary packing writes each cell with its labels: payments volume, American Express, 637. The next cell repeats American Express, and so does every cell after it. Dependency packing writes each label once and lets the cells point to it. Its first cell costs more, 18 tokens against 15, because the headers come with it. But every further cell reuses them, and the row costs 50 tokens instead of 57. The third method, length-matched, writes facts the ordinary way and adds their neighbours until it uses as many tokens as dependency packing, to test whether more text alone helps. Here it spends its tokens on a Mastercard cell next to 637, and 5.0 no longer fits. Over every FinQA table, a cell with its labels costs 15 tokens on average, and a bare cell under 4. In MultiHiertt's nested tables the ratio is eight to one. That is the whole trade: a fixed cost for structure, then more facts per token." |
| Inside PySpark | 10 | "This is what happens to the data before any question is asked. Six datasets arrive in different shapes: JSON files, a zip archive, HTML tables and a linked Wikipedia corpus. Python readers turn all of them into three tables: documents, questions and facts. Each fact keeps the list of labels it needs, the arrows of our graph, as an array. PySpark loads the three tables as DataFrames. It explodes each fact's array into one row per arrow, 1,884,748 edges in all. An anti-join checks that every arrow points to a real fact, and none is missing. A self-join on content hashes finds 491 pairs of identical documents across datasets, which is why we never pool them. Everything is written as Parquet, partitioned by dataset and split, in 0.18 gigabytes instead of 0.95. And the job only counts if it matches an independent Python run exactly." |
| Copy, then check | 11 | "The model does not write the answer. It writes a short plan and copies each number from the evidence. Our code looks for every copied number in the evidence. 637 and 5.0 are both there, so the plan runs and gives 127.4. If the model writes a number that appears nowhere, like 640, the plan is rejected. But if it copies the wrong real number, 647, the check passes and the answer is wrong. Grounding stops invented numbers; only the labels stop wrong choices, and that is why packing matters. Our earlier design asked for character positions instead and answered only 2 of 883 FinQA questions, though that run also used a different model." |
| How we measure | 12 | "We measure in three steps, from cheapest to most expensive. First, a coverage audit with no model at all: after packing, is every number the gold answer needs still in the evidence? For the Visa question the gold program divides 637 by the constant 5, so only 637 has to survive. We run this on every development question, 9,268 of them, at five budgets and three methods. Here each HybridQA question is one dot. Most are kept by both methods or lost by both, and they say nothing about the difference. What matters are the questions only one method keeps: 146 only by dependency packing, 7 only by ordinary. Second, Block A: 50 sampled questions per dataset, answered by Gemini 3.5 Flash-Lite, a hosted model used without any fine-tuning, once with each packing method. Third, Block B: on the same evidence, Gemini 3.1 Flash-Lite with our executor, against the same model answering directly." |
| Results | 13 | "Here is the gold evidence kept against the budget, on all six datasets. Dependency packing is on top at the chosen budgets everywhere, and the curves meet as the budget grows. This is the gap at each dataset's chosen budget. It is largest where documents are far larger than the budget, HybridQA and MultiHiertt, and smallest on FinQA and ConvFinQA, whose documents are mostly prose. At 200 tokens the fixed cost of structure loses on ConvFinQA and MultiHiertt. At 4,000 tokens the gap is zero on the four smaller datasets. Answers move the same way: dependency packing is at least as good on all six datasets, but with 50 questions only TAT-QA's gain clears zero." |
| A real question, replayed | 14 | "This is a real TAT-QA question from our answer experiment, with a budget of 400 tokens. It asks for the ratio of inventory reserves to accrued compensation in 2018. Both methods retrieved the same two paragraphs, which take 355 tokens. Ordinary packing spent the rest on three labelled cells and stopped at 398 tokens. Accrued compensation, 358, needed 17 more tokens, so it did not fit. The model said the evidence does not contain accrued compensation, and abstained. Dependency packing paid 33 tokens for the labels once and 3 tokens per cell, so 358 fit in the same budget. The model divided 948 by 358 and got 2.65, the gold answer." |
| A result we withdrew | 15 | "Block B first showed the executor 22 points ahead on MultiHiertt. Looking at the answers, direct answers often wrote a percentage, minus 29.92, where the gold answer is the fraction minus 0.2992. The official scorer compares those as text and marks them wrong, while executor programs are scored on a different path. Scored by the same numeric rule on both sides, the gap falls to 6.2 points, with an interval from minus 6.2 to plus 20. So we withdrew the claim." |
| Conclusion | 16 | "To close. The problem: large tables must fit a model's fixed context window, and numbers without labels mean nothing. The reference study kept labels by repeating them with every number, at four to eight times the tokens per cell. Our method writes each label once and links every number to it, as a dependency graph packed under the budget. PySpark builds and verifies the 1.36 million facts and 1.88 million label links behind it. And the result: more of the evidence a question needs survives on all six datasets, and Gemini 3.5 Flash-Lite answers at least as well, clearly better on TAT-QA." |

## Likely questions

- *How do your numbers compare with the reference paper's?* They do not compare directly: different models, splits and metrics (they report exact match of parsed steps on 256 FinQA validation samples; we report official scorers). We use their findings as motivation, not as a baseline.
- *Why not a bigger sample?* Free-tier limit of 500 requests per day per model. Runs resume from saved answers, so more data only costs more days.
- *Is the comparison fair to ordinary packing?* It gets every structural label inline, at the same budget, model and prompt. Only the packing differs.
- *Why does dependency packing lose at 200 tokens?* Its first fact from a table carries all its headers (18 tokens against 15 in the Visa row). With room for only a few facts, that fixed cost crowds out other evidence.
- *Why is Spark slower?* 1.4 million rows fit in one machine's memory; Spark's start-up and coordination costs dominate. Its value here is a checked, partitioned store.
- *Could gold answers have leaked?* Labels are stored separately and joined only at scoring. A check of 443 saved prompts found no label fields.
