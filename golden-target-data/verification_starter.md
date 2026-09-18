## Tool contract

```
<cmd> <pack_dir>     ->  JSON on stdout
```
```json
{
  "unique_target_count": 123,
  "golden_records": [{"gene":"...","primary_accession":"...","sources":["..."]}],
  "findings": [
    {"gene":"...","observed":"<the defective value as it appears in the file>",
     "correct":"<the corrected value>",
     "retrieved_evidence":"<what the authority literally returned when you resolved the entity>",
     "evidence_source":"<where you got it>",
     "severity":"...","classification":"..."}
  ]
}
```

## Runtime budget & the hidden dataset

Your tool must complete each pack **within 5 minutes** when graded — and it will be executed on a second, **hidden dataset with the same schema** that you never see. All objective points are measured there.

## Notes

- The `pmid` values in `source_publications.csv` are **internal reference numbers, not
  literature links**. Some coincide with real PubMed records for unrelated papers, so a
  mismatched paper behind a pmid is an artifact of the synthetic numbers — not a defect.
  Do not fetch them and do not flag them; ambiguous mentions are resolved from the shipped
  `context_sentence` text.
- Re-verify at submission time — reference databases evolve.
