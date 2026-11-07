# Project working instructions

## Purpose

Develop a course project on numerical reasoning over financial data.
The exact research question and architecture are not decided yet.

Build a useful, technically sound project with a defensible contribution.
Do not assume that a complicated architecture is a better architecture.

## Communication

- Use easy, natural English without reducing technical depth.
- Explain unfamiliar technical terms when first introduced.
- Explain what we are doing, why it matters, and how we will check it.
- Keep progress updates short.
- Make research proposals understandable to a student who must defend them.

## Existing materials

Workspace: /home/p_2626/BigDataEndSem
Existing environment: /home/p_2626/bigdata-env
Existing code: ../Current_implementation
Report template: ../Current_implementation/Chiru-End-Sem/acl2023

Dataset repositories are in the parent workspace.
Inspect them to confirm their identities and available files.
we are having FinQA,ConvFinQA,TAT-QA,HybridQA as our main datasets given by prof and TAT-HQA , MultiHiertt as our added datasets.Our architecture will be based on all these datasets.
Treat existing repositories, raw datasets, and the current implementation
as reference material. Do not modify them.

Write new project work inside this final directory.

## Research standards

- Separate verified facts, assumptions, and proposed ideas.
- Support important literature claims with sources.
- Inspect original papers and official implementations where possible.
- Search for work that may already implement a proposed idea.
- Never claim an idea is globally novel because a search found no match.
- Explain the difference from the closest relevant work.
- Do not invent references, experimental results, or completed checks.
- Prefer a focused contribution with a clear test over many weak additions.

## Experimental standards

- Keep reference answers and gold annotations out of test-time inputs.
- Preserve official dataset splits and evaluation rules where applicable.
- Check overlap before combining related datasets.
- Distinguish published results from results reproduced by us.
- Compare the proposed contribution with a simpler controlled baseline.
- Record configurations, model versions, prompts, and output locations.
- Explain failures and limitations honestly.

## Engineering

- Inspect existing work before deciding to reuse or replace it.
- Use a shared core where justified; keep dataset-specific readers
  and evaluators when needed.
- Do not force all datasets into an unsuitable common representation.
- Choose Spark/Hadoop responsibilities based on the workload and
  course requirements, not merely to mention those technologies.
- Break implementation into focused, verifiable tasks.
- Update docs/state.md after a meaningful milestone.

## Planning phase

During discovery and planning:
- Read files and inspect the environment without changing it.
- Write planning documents only.
- Do not install packages, train models, call paid inference APIs,
  or start implementation.
- Record missing constraints rather than inventing them.