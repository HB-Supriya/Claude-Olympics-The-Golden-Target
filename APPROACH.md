# Approach summary

**Written for: the Claude Olympics graders assessing reconciliation accuracy, defect surfacing and
investigation rigor.**

Tool: `python3 solve.py <pack_dir>`. Result on `exam/`: **609 unique targets, 65 findings**, every one
carrying observed value, correction, and the authority's literal response. Zero dependencies, ~39 s
cold against a 300 s budget.

## 1. Audit strategy — what was checked for every row, and why the list is complete

I profiled the pack before writing a detector, with no network access, and committed the result
(`reports/profile_exam.md`). That pass asks only *what could be wrong*: row counts, identifier shape,
blank fields, and — most usefully — the two internal contradictions that survive a self-join. One
accession claiming several gene symbols (2 cases) and one symbol claiming several accessions (8 cases)
are exactly the shapes that a wrong mapping or a duplicate identity makes.

Then, because the brief says each defective row is internally consistent, I enumerated the checks by
asking what the authority can independently tell me about a row, field by field, and made each one a
detector: **is the accession current** (merged/demerged/deleted/secondary), **is it an accession at
all** (well-formed, known), **is it the right granularity** (protein entry vs splice isoform), **does
its organism match**, **does its gene symbol match** (approved / former synonym / belongs elsewhere),
**does its external cross-reference match**, **is one target keyed twice**, and **does a literature
mention name one protein or several**.

I claim the list is complete on two grounds. First, coverage: every column in the five files is either
checked against the authority, used as corroborating evidence, or explicitly excluded with a reason
(§4). Second, exhaustion: I ran targeted sweeps for classes the detectors would *not* have caught, and
they came back empty — all 600 live `source_uniprot` rows agree with the authority on sequence length,
review status and entry name; all 641 resolved entries are taxon 9606; all 459 literature mentions but
one resolve to a single target. Zero results are reported as zero rather than padded.

## 2. Validating identities — fields relied on, and where I cross-checked

Resolution runs against the **EBI Proteins API** in batches of 80 accessions, reading `accession`,
`id`, `organism.taxonomy`/`names`, `gene.name`/`synonyms`, `protein.recommendedName`/`alternativeName`,
`secondaryAccession`, `dbReferences` and `comments`.

The Proteins API cannot say what happened to an accession that no longer exists — obsolete accessions
simply do not come back. So those escalate to **UniProt REST**, which returns `inactiveReason` and
`mergeDemergeTo`. One trap matters: UniProt answers an obsolete accession with `303 See Other`, and the
*body of the 303 is the inactive record*. Following the redirect — every client's default — discards
`inactiveReason` and leaves a merge indistinguishable from an ordinary secondary accession. My first
run mislabelled all 30 merges as `secondary_accession` for exactly this reason. The client now
suppresses redirect-following for those lookups and reads the 303 itself.

Three independent cross-checks arbitrate conflicts rather than relying on one field:

- **Gene-symbol → accession** (`gene_exact:SYM AND organism_id:N AND reviewed:true`), which finds the
  entry a symbol actually belongs to.
- **Cross-reference → accession** (`xref:chembl-CHEMBLnnn`). UniProt curates its own ChEMBL
  cross-references, so a ChEMBL id is checkable in both directions. This independently confirmed the
  PIM1 wrong mapping and caught `CHEMBL3012`, which the pack attaches to both PDE7A and PDE10A;
  UniProt says it belongs to Q13946 (PDE7A) and PDE10A's is CHEMBL4409.
- **The row's own protein-name field** as a third witness (see §3).

Merge chains are followed to a live entry, not one hop: `E9PGB9 → Q86YH7 → P56524` (HDAC4), and
`D4Q9M8 → P01562 → A0A087WWS6`, where P01562 is *demerged* into two entries and the row's own gene
symbol (IFNA13) picks the correct side of the split.

## 3. Decision rules — defect vs legitimately messy

1. **No authority answer, no finding.** An unreachable endpoint costs recall, never precision.
   `Finding` cannot be constructed without all four evidence fields, so this is structural.
2. **Normalize before comparing.** Organism spelling, hyphenation and casing are reconciled first.
   Only what survives normalization can become a finding.
3. **A recorded synonym is a stale label, not a wrong mapping.** If the authority still lists the
   row's symbol for that entry, the identity is right and only the label is old: low severity, and the
   accession is left alone. The claim stops there deliberately — `gene.synonyms` carries no historicity
   flag, so the evidence cannot show whether a synonym was ever *official*, and the finding does not
   assert that it was.
4. **Arbitrate with the third witness.** When symbol and accession disagree, the row's protein-name
   field decides which is wrong. ChEMBL row `CHEMBL2147` says gene `PIM1`, name
   "Serine/threonine-protein kinase pim-1", accession `Q9P1W9` — which is PIM2. Two of three fields
   agree, so the *accession* is defective (correct: `P11309`). Where the name is silent I trust the
   accession, as the machine key, and report the symbol — stated explicitly in the finding.
5. **Severity is blast radius**: *high* = points at the wrong protein; *medium* = right identity,
   dead/duplicated/mis-cross-referenced key; *low* = stale-but-valid label.
6. **Report each defective row once**, under its most consequential label, with every affected row
   listed — 82 row-level detections became 65 findings.

## 4. Something investigated and deliberately not flagged

**Protein-name disagreement.** 55 rows carry a `pref_name`/`target_name` matching neither the
accession's recorded names nor its own gene symbol. That looked like a defect class worth 55 findings.
Reading them, every one is legitimate variation: alternative names UniProt itself lists
(`D(2) dopamine receptor` vs `Dopamine receptor D2`), well-known aliases (`TGR5` for
`G protein-coupled bile acid receptor 1`), or the symbol restated (`IGLV1-47 protein`). BindingDB and
ChEMBL simply name proteins in their own house style, which is messy, not wrong. Flagging it would
have added 55 false positives — nearly doubling the report with noise — so protein names are used only
to *arbitrate* which of two conflicting keys is defective, never as a finding in themselves.

Also excluded, per the brief and asserted by a test: `pmid`/`journal`/`year` are never fetched and
never flagged.

## 5. Validating the tool before running it on the exam

A 45-row `tests/fixtures/mini_pack/` hand-built to contain one clean instance of every defect class,
several genuinely clean rows, and a `pmid` decoy. It paid for itself immediately, exposing three real
bugs the 600-target exam pack hid: the two-hop merge chain stopping at the first hop; a malformed
accession accepted as a golden record's primary key; and the isoform class, which I had not
implemented at all until a shape check surfaced `Q05086-3` and `Q13422-3` — valid identifiers naming
splice variants rather than proteins, which I was silently *dropping*, losing two real targets.

72 tests run fully offline against a recorded response set, and the replay client raises on any
un-recorded request, so a change that starts issuing new lookups cannot pass unnoticed. Coverage
includes each detector's negative cases, the output contract, and the tool invoked as a real
subprocess with its stdout parsed as JSON — plus an empty-pack case and a static Python 3.11 grammar
check, since the declared runtime is older than my local interpreter.

## 6. Working with Claude

I delegated mechanical breadth: batch-resolving 639 accessions, sweeping 2,578 rows for column-level
disagreement, and drafting the detector scaffolding once I had fixed the rules. I verified every
substantive claim myself by hand-querying the endpoints: the merge status of each obsolete accession,
the ChEMBL cross-reference ownership, the `PSA` alias sitting on both `KLK3_HUMAN` (short name PSA) and
`P55786` (whose entry name is literally `PSA_HUMAN`, gene NPEPPS), and the isoform lists behind
`Q13422-3`. Two suggestions I rejected: dropping malformed accessions silently, and taking UniProt's
redirect target as the merge answer — the first loses targets, the second loses the evidence. I also
re-derived every one of the 65 findings against the authority before accepting the report.

## 7. What I would harden before production

**Ambiguous-mention scoring is the weakest link.** Resolving `PSA` works by weighted token overlap
against the authority's names, keywords and functional annotation, with a required 1.5× margin over
the runner-up. It resolved all 7 rows correctly, but it is a heuristic; in production I would use a
curated alias table (HGNC plus an internal synonym registry) as the primary route and keep scoring
only as a fallback, with anything below the margin queued for human review rather than dropped.

Beyond that: pin the authority's release version in every finding so a correction stays reproducible
as the database evolves; persist findings as an auditable review queue with accept/reject decisions
feeding back into the rules rather than a fresh report each run; add HGNC and NCBI Gene as
corroborating authorities so a symbol claim has two independent witnesses; make the run idempotent and
incremental so only changed rows are re-verified; and add monitoring on finding-rate per class, since a
sudden jump in `obsolete_accession` usually means an upstream extract went stale rather than that the
data got worse.
