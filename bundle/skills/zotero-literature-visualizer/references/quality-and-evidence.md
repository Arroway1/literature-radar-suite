# Quality and evidence rules

## Journal Impact Factor

Use only an official journal, publisher, or Clarivate page that explicitly identifies the Journal Impact Factor and year. Record journal, displayed value, metric year, source URL, verification date, and a short evidence note.

Do not substitute CiteScore, SJR, SNIP, an OpenAlex metric, a search snippet, or a third-party ranking site for official JIF evidence. If official evidence is unavailable, leave the value blank or mark it unverified.

See `if-verification.md` for the evidence-table format.

## CAS partition

Display `cas_partition` and `cas_top` only when they are supplied by a reliable, dated CAS source or by the user. Record source and edition where practical. Do not infer a CAS partition from JCR quartile, JIF, CiteScore, or journal prestige.

## Paper-level synthesis

For PDF-backed cards, inspect at least:

- title and abstract;
- methods or study design;
- data/sample/case description;
- results or findings;
- discussion, limitations, and conclusion.

Write claims at the specificity supported by the paper. Preserve reported uncertainty and avoid implying causal evidence from descriptive or correlational designs.

For abstract-only cards, explicitly attribute claims to the abstract and avoid invented datasets, software, locations, sample sizes, limitations, or numerical results.

For metadata-only cards, provide bibliographic navigation rather than a pseudo-summary.

## Classification

Use stable bilingual theme and method labels across the collection. A paper may have one primary method and additional method labels. Base labels on title, abstract, Zotero tags, and extracted text, but do not present an inferred label as an author-stated method.

Keep “unknown” or “not reported” distinct from missing metadata. Avoid using a generic review-level paragraph as the findings or limitations of every paper.

## Audit trail

Retain source URLs, access dates, evidence levels, and local processing logs in the run directory. The final report should state how many records have full text, abstract-only evidence, missing abstracts, verified JIF, CAS data, and resolved Zotero/PDF links.
