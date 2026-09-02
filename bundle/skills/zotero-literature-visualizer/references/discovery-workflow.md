# Topic discovery and evidence intake

## Default scope

When the user gives no constraints, use the last year, up to 30 strong papers, and a quality-first threshold such as official IF >= 5. Treat these as defaults, not universal requirements; explicit user scope always wins.

Build broad keyword groups with synonyms, acronyms, and adjacent terms. Record the inclusion/exclusion logic and retain the candidate set for auditability.

## Discovery sequence

1. Initialize a config.
2. Review and refine keyword groups, years, article types, and journal criteria.
3. Collect a broad OpenAlex candidate set and Unpaywall availability metadata.
4. Verify journal-quality evidence separately.
5. Finalize the strongest relevant records regardless of OA status.
6. Match locally available PDFs supplied by the user; otherwise retain abstract-only or metadata-only evidence.
7. Read the available evidence, classify papers, write bilingual cards, and build the dashboard.

```powershell
& '<python>' '<skill-dir>\scripts\systematic_literature_review.py' init-config `
  --topic '<topic>' --years 1 --min-if 5 `
  --output '<run-dir>\review-config.json'

& '<python>' '<skill-dir>\scripts\systematic_literature_review.py' collect `
  --config '<run-dir>\review-config.json' `
  --output-dir '<run-dir>' --max-results 120

& '<python>' '<skill-dir>\scripts\systematic_literature_review.py' finalize `
  --candidates '<run-dir>\metadata\all-candidates.json' `
  --if-evidence '<run-dir>\metadata\journal-if-evidence.csv' `
  --output-dir '<run-dir>' --min-if 5 --limit 30 --queue-all-manual
```

Do not enable automatic downloading merely because a URL exists. This skill does not claim to control an authenticated browser or download subscription PDFs. The user supplies any legally obtained local PDF files to be analyzed.

## Evidence levels after access

- `full_text`: a local PDF was parsed and the relevant sections were inspected.
- `abstract_only`: no readable PDF; synthesis is limited to the supplied abstract.
- `metadata_only`: neither full text nor abstract supports substantive interpretation.

Do not upgrade an evidence label merely because a landing page or DOI is present.
