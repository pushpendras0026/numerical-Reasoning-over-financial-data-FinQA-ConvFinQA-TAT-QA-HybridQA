# Presentation script

Speaker A: slides 1 to 8. Speaker B: slide 9 to the end. Speak slowly. Pause after every number that matters.

## Speaker A

**Slide 1. Title**

Good morning. My name is ___, and with my colleague ___ I will present our work on dependency-preserving evidence packing for numerical question answering over financial reports.

The title is long, but the idea behind it is small enough to hold in one hand. A number means nothing on its own. Our project is about what it costs to keep a number's meaning, and how that cost can be paid only once.

**Slide 2. The task**

Imagine reading the annual report of a large company in order to answer one question: what was the margin, how fast did revenue grow, what is the ratio of these two lines? A language model can do this work, but it has one hard limit. It can only reason over the text placed in front of it, and an annual report is far longer than the space we can give it.

So before the model answers anything, a system must make a decision. Which facts go in, and how should they be written? That decision is quiet and easily overlooked. We found it to be one of the most interesting parts of the whole problem.

**Slide 3. The problem**

Look at these two numbers, 637 and 647. They sit side by side in a table from a Visa annual report. One is the payments volume of American Express and the other is its total volume. If the model receives the numbers alone, nothing tells them apart, and a single wrong choice gives a wrong answer that looks perfectly reasonable.

The obvious remedy is to write the labels beside every number. That works, and it is expensive. Depending on the dataset, a labeled cell costs between two and eight times as much as the bare number. Every label we repeat takes the place of evidence that the question may need.

**Slide 4. Prior approach**

Our starting point was the study by Arun and colleagues. They turn each table into sentences such as "the revenue of 2019 is 100", retrieve one chunk of text, and fine-tune T5 or Llama 2 to reason over it. We learned a great deal from this paper, and we will show its central finding shortly. It also gave us our question: must the label really be paid for again with every number?

**Slide 5. Our contribution**

We believe it need not. Our contribution is a simple change in how evidence is written. Each number is linked to the labels it requires, and each label is written once and shared. Around that idea we built a verified PySpark data layer over six datasets, a coverage audit of all 9,268 development questions, and a paired experiment measuring the effect on real answers.

**Slide 6. Objectives**

We set ourselves five objectives: one pipeline across all the datasets, a fair comparison of packing methods at a fixed budget, a verified Big Data preparation, a paired answer test, and answers that can be traced to their evidence. We wanted every claim in this talk to rest on something that can be checked.

**Slide 7. Datasets**

We used the four assigned datasets, FinQA, ConvFinQA, TAT-QA and HybridQA, and we added two that are deliberately harder: TAT-HQA, which asks hypothetical questions, and MultiHiertt, which has deep hierarchical tables. Some of these datasets share documents, and for that reason we never pool their results. An impressive average built on duplicated data would have told us nothing.

**Slide 8. Pipeline**

Here is the full pipeline. Please notice the one highlighted box. Everything else stays fixed: the same retrieval, the same model, the same budget. Only the packing changes, so that any difference we measure belongs to the packing. Gold answers meet the predictions only at the very end, during scoring. My colleague will now take you through the method.

## Speaker B

**Slide 9. Dependency graph and packing**

Thank you. We compare three methods. Ordinary packing writes the labels inside every cell. Dependency packing brings in each label once. Length-matched packing adds neighboring text until it is as long as dependency packing, which tells us whether more text alone would have helped.

Now I would like to show you how all of this works, from the problem, through the paper we started from, to our method on real data.

**Video: `crux.mp4` (4:32). Read each part as its clip plays.**

*A number needs its labels*

This is a real table from a Visa annual report. The question asks for the average payment volume per transaction of American Express. Our retriever ranks two cells highest: 637 and 647.

Without their labels, they are simply two similar numbers. Only the column headers tell us that 637 is payments volume and 647 is total volume. The answer, 637 divided by 5.0, which is 127.4, depends on the labels as much as on the values.

*The reference pipeline*

We began from the 2023 study by Arun and colleagues at Georgia Tech. It answers questions about an annual report in five steps.

First, it finds the tables in the PDF. Then it writes each table as sentences: the revenue of 2019 is 100, the cost of 2019 is 50. It splits this text into chunks, and FAISS picks the one chunk closest to the question. A fine-tuned model, T5 or Llama 2, writes the solution steps, and a regular expression reads them.

Now, here is the finding that stayed with us. The fine-tuned T5 chooses the right operation about 95 percent of the time, and the right numbers about two thirds of the time. Yet its own arithmetic is right only 12 percent of the time. Give that arithmetic to a calculator, and the figure rises to 62 percent.

Three of its choices shaped our project. Its sentences repeat the labels for every number. Its search passes along only part of the report. And its calculator teaches a clear lesson: let the model choose the numbers, and let code compute.

*Our idea: a graph of labels*

Here is our idea, on the same table. Every cell becomes a fact, and every label becomes a fact too. Each number has arrows to the labels it needs. American Express is one shared node, and every number in the row points to it.

A question arrives, and the retriever ranks 637 first. We take 637 and follow its arrows, so its header and its row come with it: 18 tokens. Next comes 647. American Express is already there, so only the new header is paid for: 29 tokens. The remaining cells follow, and the whole row costs 50.

Each label has entered exactly once. Ordinary packing would have written American Express four times and spent 57. The model now receives a small table, within budget, in which every number can still be read.

*A real question, replayed*

This is a real TAT-QA question from our experiment, with a budget of 400 tokens. It asks for the ratio of inventory reserves to accrued compensation in 2018.

Both methods retrieve the same two paragraphs, which take 355 tokens. Ordinary packing spends the rest on three labeled cells and stops at 398. The number it still needs, 358, requires 17 more tokens. It does not fit.

So the model says, correctly, that the evidence is incomplete, and it abstains. Dependency packing pays 33 tokens for the labels once and 3 for each cell. Now 358 fits. The model divides 948 by 358 and gives 2.65, the correct answer. The same model, the same budget, and a different way of writing the evidence.

**Slide 10. PySpark**

Behind that small example stands a large amount of data. PySpark explodes the dependency lists into 1.88 million label links over 1.36 million facts, and it confirms that not one link is broken. It also found 491 pairs of identical documents across datasets, which is the measured reason we never pool results.

I should be candid about speed. At this size, plain Python finished in 15.8 seconds and Spark's best time was 37. What Spark gave us was a verified, partitioned store, in one fifth of the space, and every run must match an independent Python implementation or it fails.

**Slide 11. Grounded answers**

The model does not write the final answer. It writes a short plan and copies each number from the evidence, and our code checks and computes. If the model invents a number, the plan is rejected. If it copies a wrong number that is really there, the check passes. Only the labels can prevent that mistake, which brings us back to the heart of this work.

**Slide 12. Experimental setup**

We measured in three steps, from the cheapest to the most expensive. First, a coverage audit with no model at all, over all 9,268 questions. Second, a paired test on 50 questions per dataset with Gemini 3.5 Flash-Lite. Third, a comparison of our executor against direct answering, using Gemini 3.1 Flash-Lite. These models were used as served, with no fine-tuning.

**Slide 13. Result 1**

The first result is the one we find most satisfying. Dependency packing keeps more of the needed evidence on all six datasets at the chosen budgets. On HybridQA, among the questions kept by only one method, 146 favor dependency packing and 7 favor ordinary packing.

The method also behaves as the theory says it should, including where it fails. As the budget grows, the gap closes, because nothing needs to be left out. At 200 tokens, on two datasets, the cost of structure outweighs its benefit and we lose. We were glad to see that, because it shows the method has limits we can explain.

**Slide 14. Result 2**

Better evidence must still lead to better answers. Scores were at least as high on all six datasets, and on TAT-QA the gain was 11.3 points, the one improvement that is statistically clear. With 50 questions per dataset, the others remain within noise. The model also abstained less often, 12 times instead of 22 out of 295. It had found what it needed.

**Slide 15. Result 3**

This slide is the one we are perhaps proudest of. Our executor first appeared to be 22 points ahead on MultiHiertt. When we read the answers, we found that the scorer was marking percentages wrong because of how they were written. Under one fair rule for both sides, the gap became 6.2 points, with an interval through zero. So we withdrew the claim. The executor gave no consistent gain, and we report exactly that.

**Slide 16. Conclusion**

Let me return to where we began. A number means nothing without its labels, and labels cost space. By writing each label once and linking every number to it, we kept more of what a question needs, in the same budget, across six datasets.

What we value most is how simple the idea is. Nothing about the model changed. We changed how a table is written down, and in doing so we learned how much care a single number deserves.

In future work we would like to use larger samples and make the graph aware of the budget. Thank you for your attention. We would be glad to take your questions.
