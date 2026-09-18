# Data profile — `exam`

Derived from the files alone: no external lookups. This is the pass that decides
*what to check*; the authority decides *what is wrong*.

## Row counts

| source | rows |
|---|---|
| `source_chembl.csv` | 292 |
| `source_uniprot.csv` | 610 |
| `source_bindingdb.csv` | 1239 |
| `source_internal.csv` | 437 |
| `source_publications.csv` | 674 |

## Identifier shape

- distinct accession values: **639**
- isoform-form values (`ACC-n`, valid but wrong granularity for a target): **2** ['Q05086-3', 'Q13422-3']
- values that are not UniProtKB accessions at all: **0** 
- rows with a blank gene symbol: **12** {'bindingdb': 6, 'internal': 6}

## Internal disagreements (candidates to check against the authority)

### One accession, several gene symbols — 2

| accession | symbols claimed | sources |
|---|---|---|
| `Q969F8` | KISS1, KISS1R | bindingdb, chembl, internal, uniprot |
| `Q9P1W9` | PIM1, PIM2 | bindingdb, chembl, internal, uniprot |

### One gene symbol, several accessions — 8

| gene | accessions |
|---|---|
| `ABTB3` | A4FU41, A6QL63, B3KXG3 |
| `CCDC169` | A6NC13, A6NCT2, A6NNP5 |
| `EPHA2` | B5A968, P29317 |
| `HNF4A` | A5JW41, B2RPP8, P41235 |
| `IFNA13` | A0A087WWS6, D4Q9M8, P01562 |
| `KISS1` | Q15726, Q969F8 |
| `PIM1` | P11309, Q9P1W9 |
| `SRPK1` | B4DS61, Q96SB4 |

## Free-text spelling variation (normalized, never reported as a defect)

- `source_chembl.organism`: 'Homo sapiens'×292
- `source_uniprot.organism`: 'Homo sapiens (Human)'×610
- `source_bindingdb.organism`: 'human'×335, 'Human'×335, 'H. sapiens'×293, 'Homo sapiens'×276

## Literature mentions

- distinct mentions: **459**
- mentions that are not the gene symbol of any target in this pack (i.e. aliases needing resolution): **1** ['PSA']

`pmid`, `journal` and `year` are deliberately not profiled and never fetched: they
are internal reference numbers, and some collide with unrelated real PubMed records.
