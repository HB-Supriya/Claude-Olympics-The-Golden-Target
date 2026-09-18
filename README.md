# The Golden Target — target-master reconciliation

Builds one trusted golden record per drug-discovery target from five overlapping source extracts
(ChEMBL, UniProt, BindingDB, an internal target registry, and a literature-mention table), and
reports the real defects with proof retrieved from an authoritative external source.

```bash
python3 solve.py <pack_dir>          # prints exactly one JSON object to stdout
```

```json
{
  "unique_target_count": 609,
  "golden_records": [{"gene": "...", "primary_accession": "...", "sources": ["..."]}],
  "findings": [{"gene": "...", "observed": "...", "correct": "...",
                "retrieved_evidence": "...", "evidence_source": "...",
                "severity": "...", "classification": "..."}]
}
```

Zero third-party dependencies (stdlib only). Python 3.11.

---

## 1. Result on the shipped `exam/` pack

609 unique targets from 2,578 identity rows carrying 639 distinct accession values, and **45
findings**, each carrying its observed value, its correction, and the authority's literal response.
Cold, with an empty cache and live network, the run takes **38s** against the 5-minute budget.

| classification | n | severity | what it is |
|---|---|---|---|
| `wrong_accession_mapping` | 2 | high | the accession denotes a *different protein* than the row describes |
| `obsolete_accession` | 30 | medium | accession merged/demerged away; corrected to the live successor |
| `isoform_accession` | 2 | medium | keyed on a splice isoform (`Q13422-3`) instead of the protein entry |
| `wrong_crossreference` | 1 | medium | ChEMBL id belongs to a different UniProt entry |
| `ambiguous_mention` | 2 | medium | a literature alias shared by two proteins, resolved from context |
| `missing_gene_symbol` | 6 | low | blank symbol, filled from the authority |
| `stale_gene_symbol` | 2 | low | the row's symbol is a recorded synonym, not the approved symbol |

Full evidence for every finding: [`reports/findings_exam.md`](reports/findings_exam.md) (readable) and
[`reports/findings_exam.json`](reports/findings_exam.json) (the tool's exact stdout).
Structural profile of the pack, produced with no network access:
[`reports/profile_exam.md`](reports/profile_exam.md).

Two classes are implemented and tested but **found zero instances here**, honestly reported as zero
rather than padded: `organism_mismatch` (all 641 resolved entries are taxon 9606) and
`invalid_accession` (every accession value resolves). Both fire in the test pack, so they are ready
for a pack that does contain them.

### What is deliberately *not* reported

The detectors produce 82 candidates; 45 are published. The gap is not a confidence threshold — it is
three rules that withhold a claim the evidence does not support:

**One defective row is one finding.** A row carrying a retired accession usually carries that era's
gene symbol as well. Reporting both turns one injected defect into two findings, and the symbol half
is the weaker claim. So a `stale_gene_symbol` finding is withheld wherever that same row is already
reported for its accession — 20 of them on this pack. The 2 that remain (`WHSC1`→`NSD2`,
`SEPT9`→`SEPTIN9`) stand on their own rows, with a correct accession.

**Only what the payload proves.** UniProt's `gene.synonyms` carries no historicity flag: it mixes
symbols that were once official with aliases that never were. So the evidence text claims only what
is literally true — "listed by the authority as a synonym of X, not its approved symbol" — and never
asserts that a symbol was formerly official, because the authority does not say so.

**Only documented labels.** The internal vocabulary is wider than the report's nine classifications.
Anything outside them is mapped to a documented equivalent (`secondary_accession` →
`obsolete_accession`) or withheld and counted on stderr. `contract.py` fails the run rather than
print a label the report never defined.

## 2. The authority

**EBI Proteins API** — `https://www.ebi.ac.uk/proteins/api/proteins` — is the primary source, queried
in batches of 80 accessions. It answers, for a live entry: its organism, its approved symbol, the
other symbols it has been known by, its cross-references to other databases, and its splice isoforms.

It cannot answer one question by design: *what happened to an accession that no longer exists*. A
merged or deleted accession simply does not come back from `/proteins`. For those we escalate to
**UniProt REST** — `https://rest.uniprot.org/uniprotkb/{acc}.json`, the same UniProt/EBI system of
record — which returns `inactiveReason` with the successor accession.

One detail worth knowing if you read the code: UniProt answers an obsolete accession with
`303 See Other` pointing at the successor, and **the body of that 303 is the inactive record**.
Following the redirect (the default for every HTTP client) silently discards `inactiveReason` and
leaves you unable to tell a merge from an ordinary secondary accession. The client therefore
suppresses redirect-following for those lookups and reads the 303 itself — see
`goldentarget/httpjson.py::_NoRedirect`.

Every finding names the endpoint that produced its evidence in `evidence_source`.

## 3. How it works

```
solve.py                     entry point: argv[1] -> one JSON object on stdout, nothing else
goldentarget/
  httpjson.py                TLS/retry/deadline/cache HTTP layer (urllib only)
  authority.py               EBI Proteins + UniProt REST -> one uniform ProteinRecord
  loaders.py                 the five CSVs -> rows with canonical field names
  normalize.py               organism/name/symbol normalization; the precision boundary
  detectors.py               the defect rules, one authority comparison each
  golden.py                  entity resolution and golden-record assembly
  findings.py                the Finding type and its enforced evidence contract
  contract.py                output-shape validation, run on every invocation
  pipeline.py                orchestration and phase budgeting
tools/report.py              regenerate reports/ artifacts
tools/record_fixtures.py     re-record the offline test fixture
tests/                       90 tests, fully offline
```

Pipeline order is deliberate: **resolve → detect row-level → cluster → detect corpus-level**. Row
detection has to come before clustering, because a row whose accession points at the wrong protein
must be re-filed under the target it actually describes — otherwise the wrong mapping corrupts a
golden record as well as producing a finding.

Three design rules do most of the work:

1. **No authority answer, no finding.** If a lookup fails or the endpoint is unreachable, the row is
   left alone. Missing evidence costs recall, never precision.
2. **"No such entry" and "no answer" are different values.** `httpjson` returns `None` when the
   authority answered and holds no such record, and `UNREACHABLE` when nothing came back. Only
   `None` licenses a conclusion. Collapsing the two would let a 429 or a DNS blip read as "this
   accession does not exist" and manufacture a high-severity `invalid_accession` out of a timeout —
   so with the network pulled, the tool emits 637 golden records and **zero** findings, not false
   ones.
3. **`Finding` refuses to be constructed** without all four evidence fields. A detector cannot emit
   an unproven claim even by accident.

Where the authority returns several candidate entries for one symbol or cross-reference, no
correction is emitted at all: `alternatives[0]` out of many is search relevance order, not evidence.

Nothing is keyed to a value seen in the exam pack — no gene allow-lists, no accession patches. Every
rule is a procedure that queries the authority, so it behaves identically on an unseen pack.

## 4. What is deliberately *not* flagged

Precision counts against you when you get it wrong, so these were each investigated and rejected:

- **`pmid` / `journal` / `year`.** Internal reference numbers, not literature links. Some collide
  with real PubMed records for unrelated papers, so any mismatch behind one is an artifact of the
  synthetic numbering. Never fetched, never flagged — asserted by a test.
- **Organism spelling.** `Homo sapiens` / `H. sapiens` / `human` / `Homo sapiens (Human)` all appear;
  all four normalize to one organism. Only a genuine cross-species mapping is a defect.
- **Protein-name variation.** 55 rows carry a name that matches neither the accession's recorded
  names nor its own symbol — `D(2) dopamine receptor` vs `Dopamine receptor D2`, `TGR5` vs
  `G protein-coupled bile acid receptor 1`, `IGLV1-47 protein`. Every one checked is a legitimate
  alternative name, a well-known alias, or the symbol restated. Names are used only to *arbitrate*
  which of two conflicting keys is wrong; disagreement alone is never a finding.
- **`length`, `reviewed`, `database`, `entry_name`.** Checked all 600 live UniProt rows against the
  authority's sequence length, review status and entry name: zero mismatches.

## 5. Validation

```bash
python3 -m pytest tests -q      # 90 tests, no network access required
```

The suite replays a **recorded** authority response set (`tests/fixtures/recorded_authority.json`),
and the replay client *raises* on any request that was not recorded — so a change that starts issuing
new lookups cannot slip past silently. Tests cover: the precision boundary in `normalize`, the
evidence contract, every detector's positive *and* negative cases, clustering, and the tool run as an
actual subprocess with its stdout parsed as JSON.

`tests/fixtures/mini_pack/` is a 45-row pack hand-built to contain one clean instance of every defect
class plus genuinely clean rows and a `pmid` decoy. It earned its keep: it exposed three real bugs the
600-target exam pack did not — a two-hop merge chain (`E9PGB9 → Q86YH7 → P56524`) that stopped at the
first hop, a malformed accession accepted as a primary key, and the isoform class entirely.

Runtime on `exam/` with a cold cache: **~39 s**, 47 HTTP requests, against a 300 s budget.

## 6. Environment notes

- **Cache.** `.gtcache/` is a development accelerant, gitignored, and absent at grading time — the
  graded run always verifies live. Entries expire after 7 days so a stale answer cannot outlive a
  real database change. `GT_NO_CACHE=1` disables it.
- **TLS.** The client clears `VERIFY_X509_STRICT` (which Python 3.13 turned on by default, and which
  rejects otherwise-trusted corporate CA certificates over cosmetically malformed extensions).
  Certificate *and* hostname verification stay fully on. `SSL_CERT_FILE` / `GT_CA_BUNDLE` are
  honoured for custom trust stores.
- **Env vars**, all optional: `GT_VERBOSE=1` (diagnostics to stderr), `GT_BUDGET_SECONDS`,
  `GT_CACHE_PATH`, `GT_NO_CACHE=1`, `GT_CA_BUNDLE`.
- **Failure behaviour.** A fatal error still prints well-formed empty JSON to stdout and returns a
  non-zero exit code, because a traceback on stdout is scored as a crash.

`legacy/` holds a superseded earlier attempt, kept only for reference; it is not part of the tool.
