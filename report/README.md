# Report draft

`main.tex` is a draft until measured live results and final acceptance are added.
The style and bibliography style were copied from the supplied ACL 2023 folder;
the original remains unchanged. The package name uses lowercase `acl2023` to
match the actual file on Linux. No ACL conference page limit is assumed to be a
course requirement. Author/affiliation need completion.

Compile in ordinary WSL after installing a TeX distribution with `pdflatex`,
`bibtex`, Times fonts, and the packages imported in `main.tex`:

```bash
cd /home/p_2626/BigDataEndSem/final/report
make
```

Current environment: `pdflatex`, `bibtex`, and `latexmk` are absent; compilation
has not been established. No PDF is supplied as a completed report.

Generate a measured CSV/LaTeX table with `scripts/aggregate_results.py` and a PDF
chart with `scripts/plot_results.py` as documented in `docs/final-testing.md`.
Inspect long generated tables before including them in the two-column report.
Pending sections: main scores, paired uncertainty, length control interpretation,
ablations, error analysis, actual usage/latency/quota, and Spark runtime/RAM/spill.
The abstract and discussion also need updating after those measurements.
