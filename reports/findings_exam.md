# Findings — `exam`

- unique targets: **609**
- findings reported: **65** (from 82 row-level detections, de-duplicated)
- by severity: high=2, low=28, medium=35
- runtime: 10.8s, 3 HTTP requests, 0 errors

| # | severity | classification | count |
|---|---|---|---|
| 1 | medium | `obsolete_accession` | 30 |
| 2 | low | `stale_gene_symbol` | 22 |
| 3 | low | `missing_gene_symbol` | 6 |
| 4 | high | `wrong_accession_mapping` | 2 |
| 5 | medium | `isoform_accession` | 2 |
| 6 | medium | `ambiguous_mention` | 2 |
| 7 | medium | `wrong_crossreference` | 1 |

---

### `wrong_accession_mapping` — KISS1 (high)

- **observed** (in file): `Q969F8`
- **correct** (per authority): `Q15726`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/search?query=gene_exact:KISS1+AND+organism_id:9606+AND+reviewed:true`
- **retrieved_evidence**:

  ```
  {"gene": {"name": "KISS1", "synonyms": []}, "organism": {"scientificName": "Homo sapiens", "taxonId": "9606"}, "primaryAccession": "Q15726", "recommendedName": "Metastasis-suppressor KiSS-1", "uniProtkbId": "KISS1_HUMAN"} ; queried accession resolves instead to {"accession": "Q969F8", "gene": {"name": "KISS1R", "synonyms": ["AXOR12", "GPR54"]}, "id": "KISSR_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "KiSS-1 receptor", "secondaryAccession": ["A5D8U2", "B2RTV1", "Q96QG0"]}
  ```

- **why**: The row's gene symbol KISS1 and protein name 'KISS1' both denote Q15726 (KISS1_HUMAN), but the accession recorded is Q969F8, which the authority resolves to a different protein (KISS1R, KISSR_HUMAN). Two of the row's three identity fields agree, so the accession is the defective one.
- **impact**: Wrong mapping — the most damaging class: every assay and publication on this row attaches to the wrong protein in the master.
- **rows** (1): `source_bindingdb.csv row 475 (Q969F8)`

---

### `wrong_accession_mapping` — PIM1 (high)

- **observed** (in file): `Q9P1W9`
- **correct** (per authority): `P11309`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/search?query=gene_exact:PIM1+AND+organism_id:9606+AND+reviewed:true`
- **retrieved_evidence**:

  ```
  {"gene": {"name": "PIM1", "synonyms": []}, "organism": {"scientificName": "Homo sapiens", "taxonId": "9606"}, "primaryAccession": "P11309", "recommendedName": "Serine/threonine-protein kinase pim-1", "uniProtkbId": "PIM1_HUMAN"} ; queried accession resolves instead to {"accession": "Q9P1W9", "gene": {"name": "PIM2", "synonyms": []}, "id": "PIM2_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Serine/threonine-protein kinase pim-2", "secondaryAccession": ["A8K4G6", "Q99739"]}
  ```

- **why**: The row's gene symbol PIM1 and protein name 'Serine/threonine-protein kinase pim-1' both denote P11309 (PIM1_HUMAN), but the accession recorded is Q9P1W9, which the authority resolves to a different protein (PIM2, PIM2_HUMAN). Two of the row's three identity fields agree, so the accession is the defective one.
- **impact**: Wrong mapping — the most damaging class: every assay and publication on this row attaches to the wrong protein in the master.
- **rows** (1): `source_chembl.csv row 7 (CHEMBL2147)`

---

### `isoform_accession` — IKZF1 (medium)

- **observed** (in file): `Q13422-3`
- **correct** (per authority): `Q13422`
- **field**: `accession`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=Q13422`
- **retrieved_evidence**:

  ```
  {"accession": "Q13422", "gene": {"name": "IKZF1", "synonyms": ["IK1", "IKAROS", "LYF1", "ZNFN1A1"]}, "id": "IKZF1_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "DNA-binding protein Ikaros", "secondaryAccession": ["A4D260", "B4E0Z1", "D3DVM5", "O00598", "Q53XL2", "Q69BM4", "Q8WVA3"]} ; the entry's ALTERNATIVE_PRODUCTS annotation lists isoforms Q13422-1, Q13422-2, Q13422-3, Q13422-4, Q13422-5, Q13422-6, Q13422-7, Q13422-8, so Q13422-3 is isoform Ik3 of Q13422 rather than a protein entry
  ```

- **why**: Q13422-3 is a splice-isoform identifier, not a primary accession: the authority lists it as isoform Ik3 of Q13422 (IKZF1, IKZF1_HUMAN). A target master keys one record per protein, so this row should carry Q13422.
- **impact**: Wrong granularity: the target is keyed to one splice variant, so assay data for the protein splits by isoform and no record represents the target itself.
- **rows** (4): `source_bindingdb.csv row 200 (Q13422-3)`; `source_bindingdb.csv row 725 (Q13422-3)`; `source_bindingdb.csv row 802 (Q13422-3)`; `source_uniprot.csv row 420 (Q13422-3)`

---

### `isoform_accession` — UBE3A (medium)

- **observed** (in file): `Q05086-3`
- **correct** (per authority): `Q05086`
- **field**: `accession`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=Q05086`
- **retrieved_evidence**:

  ```
  {"accession": "Q05086", "gene": {"name": "UBE3A", "synonyms": ["E6AP", "EPVE6AP", "HPVE6A"]}, "id": "UBE3A_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Ubiquitin-protein ligase E3A", "secondaryAccession": ["A8K8Z9", "P78355", "Q93066", "Q9UEP4", "Q9UEP5", "Q9UEP6", "Q9UEP7", "Q9UEP8", "Q9UEP9"]} ; the entry's ALTERNATIVE_PRODUCTS annotation lists isoforms Q05086-1, Q05086-2, Q05086-3, so Q05086-3 is isoform III of Q05086 rather than a protein entry
  ```

- **why**: Q05086-3 is a splice-isoform identifier, not a primary accession: the authority lists it as isoform III of Q05086 (UBE3A, UBE3A_HUMAN). A target master keys one record per protein, so this row should carry Q05086.
- **impact**: Wrong granularity: the target is keyed to one splice variant, so assay data for the protein splits by isoform and no record represents the target itself.
- **rows** (1): `source_uniprot.csv row 205 (Q05086-3)`

---

### `obsolete_accession` — ABTB3 (medium)

- **observed** (in file): `A4FU41`
- **correct** (per authority): `A6QL63`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/A4FU41.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["A6QL63"]}, "queried": "A4FU41", "redirectedTo": "/uniprotkb/A6QL63?from=A4FU41", "uniProtkbId": "A4FU41_HUMAN"} ; resolved to live entry A6QL63 -> {"accession": "A6QL63", "gene": {"name": "ABTB3", "synonyms": ["BTBD11"]}, "id": "ABTB3_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Ankyrin repeat- and BTB/POZ domain-containing protein 3", "secondaryAccession": ["A4FU41", "B3KXG3", "C9J019", "C9JK80", "E9PHS4", "Q3ZTQ4", "Q52M89", "Q6ZV99", "Q8N245"]}
  ```

- **why**: UniProt reports A4FU41 as MERGED into A6QL63. Its content now lives under A6QL63.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession A6QL63 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_uniprot.csv row 285 (A4FU41)`

---

### `obsolete_accession` — ABTB3 (medium)

- **observed** (in file): `B3KXG3`
- **correct** (per authority): `A6QL63`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/B3KXG3.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["A6QL63"]}, "queried": "B3KXG3", "redirectedTo": "/uniprotkb/A6QL63?from=B3KXG3", "uniProtkbId": "B3KXG3_HUMAN"} ; resolved to live entry A6QL63 -> {"accession": "A6QL63", "gene": {"name": "ABTB3", "synonyms": ["BTBD11"]}, "id": "ABTB3_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Ankyrin repeat- and BTB/POZ domain-containing protein 3", "secondaryAccession": ["A4FU41", "B3KXG3", "C9J019", "C9JK80", "E9PHS4", "Q3ZTQ4", "Q52M89", "Q6ZV99", "Q8N245"]}
  ```

- **why**: UniProt reports B3KXG3 as MERGED into A6QL63. Its content now lives under A6QL63.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession A6QL63 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_uniprot.csv row 373 (B3KXG3)`

---

### `obsolete_accession` — ADAM17 (medium)

- **observed** (in file): `O60226`
- **correct** (per authority): `P78536`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/O60226.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["P78536"]}, "queried": "O60226", "redirectedTo": "/uniprotkb/P78536?from=O60226", "uniProtkbId": "O60226"} ; resolved to live entry P78536 -> {"accession": "P78536", "gene": {"name": "ADAM17", "synonyms": ["CSVP", "TACE"]}, "id": "ADA17_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Disintegrin and metalloproteinase domain-containing protein 17", "secondaryAccession": ["O60226"]}
  ```

- **why**: UniProt reports O60226 as MERGED into P78536. Its content now lives under P78536.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession P78536 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 52 (O60226)`

---

### `obsolete_accession` — ADRA2A (medium)

- **observed** (in file): `B0LPF6`
- **correct** (per authority): `P08913`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/B0LPF6.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["P08913"]}, "queried": "B0LPF6", "redirectedTo": "/uniprotkb/P08913?from=B0LPF6", "uniProtkbId": "B0LPF6_HUMAN"} ; resolved to live entry P08913 -> {"accession": "P08913", "gene": {"name": "ADRA2A", "synonyms": ["ADRA2R", "ADRAR"]}, "id": "ADA2A_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Alpha-2A adrenergic receptor", "secondaryAccession": ["B0LPF6", "Q2I8G2", "Q2XN99", "Q86TH8", "Q9BZK1"]}
  ```

- **why**: UniProt reports B0LPF6 as MERGED into P08913. Its content now lives under P08913.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession P08913 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 492 (B0LPF6)`

---

### `obsolete_accession` — AXL (medium)

- **observed** (in file): `Q8N5L2`
- **correct** (per authority): `P30530`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/Q8N5L2.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["P30530"]}, "queried": "Q8N5L2", "redirectedTo": "/uniprotkb/P30530?from=Q8N5L2", "uniProtkbId": "Q8N5L2_HUMAN"} ; resolved to live entry P30530 -> {"accession": "P30530", "gene": {"name": "AXL", "synonyms": ["UFO"]}, "id": "UFO_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Tyrosine-protein kinase receptor UFO", "secondaryAccession": ["Q8N5L2", "Q9UD27"]}
  ```

- **why**: UniProt reports Q8N5L2 as MERGED into P30530. Its content now lives under P30530.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession P30530 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 146 (Q8N5L2)`

---

### `obsolete_accession` — BRD2 (medium)

- **observed** (in file): `A2AAU0`
- **correct** (per authority): `P25440`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/A2AAU0.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["P25440"]}, "queried": "A2AAU0", "redirectedTo": "/uniprotkb/P25440?from=A2AAU0", "uniProtkbId": "A2AAU0_HUMAN"} ; resolved to live entry P25440 -> {"accession": "P25440", "gene": {"name": "BRD2", "synonyms": ["KIAA9001", "RING3"]}, "id": "BRD2_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Bromodomain-containing protein 2", "secondaryAccession": ["A2AAU0", "B0S7P0", "B1AZT1", "O00699", "O00700", "Q15310", "Q5STC9", "Q63HQ9", "Q658Y7", "Q6P3U2", "Q969U4"]}
  ```

- **why**: UniProt reports A2AAU0 as MERGED into P25440. Its content now lives under P25440.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession P25440 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 1127 (A2AAU0)`

---

### `obsolete_accession` — CA9 (medium)

- **observed** (in file): `Q5T4R1`
- **correct** (per authority): `Q16790`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/Q5T4R1.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["Q16790"]}, "queried": "Q5T4R1", "redirectedTo": "/uniprotkb/Q16790?from=Q5T4R1", "uniProtkbId": "Q5T4R1_HUMAN"} ; resolved to live entry Q16790 -> {"accession": "Q16790", "gene": {"name": "CA9", "synonyms": ["G250", "MN"]}, "id": "CAH9_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Carbonic anhydrase 9", "secondaryAccession": ["Q5T4R1"]}
  ```

- **why**: UniProt reports Q5T4R1 as MERGED into Q16790. Its content now lives under Q16790.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession Q16790 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 364 (Q5T4R1)`

---

### `obsolete_accession` — CCDC169 (medium)

- **observed** (in file): `A6NC13`
- **correct** (per authority): `A6NNP5`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/A6NC13.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["A6NNP5"]}, "queried": "A6NC13", "redirectedTo": "/uniprotkb/A6NNP5?from=A6NC13", "uniProtkbId": "A6NC13_HUMAN"} ; resolved to live entry A6NNP5 -> {"accession": "A6NNP5", "gene": {"name": "CCDC169", "synonyms": ["C13orf38"]}, "id": "CC169_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Coiled-coil domain-containing protein 169", "secondaryAccession": ["A6NC13", "A6NCT2", "B7ZW45", "B7ZW49", "B9EJF2", "Q9H1T4", "Q9H1T5"]}
  ```

- **why**: UniProt reports A6NC13 as MERGED into A6NNP5. Its content now lives under A6NNP5.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession A6NNP5 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_uniprot.csv row 233 (A6NC13)`

---

### `obsolete_accession` — CCDC169 (medium)

- **observed** (in file): `A6NCT2`
- **correct** (per authority): `A6NNP5`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/A6NCT2.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["A6NNP5"]}, "queried": "A6NCT2", "redirectedTo": "/uniprotkb/A6NNP5?from=A6NCT2", "uniProtkbId": "A6NCT2_HUMAN"} ; resolved to live entry A6NNP5 -> {"accession": "A6NNP5", "gene": {"name": "CCDC169", "synonyms": ["C13orf38"]}, "id": "CC169_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Coiled-coil domain-containing protein 169", "secondaryAccession": ["A6NC13", "A6NCT2", "B7ZW45", "B7ZW49", "B9EJF2", "Q9H1T4", "Q9H1T5"]}
  ```

- **why**: UniProt reports A6NCT2 as MERGED into A6NNP5. Its content now lives under A6NNP5.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession A6NNP5 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_uniprot.csv row 586 (A6NCT2)`

---

### `obsolete_accession` — DYRK1B (medium)

- **observed** (in file): `O75258`
- **correct** (per authority): `Q9Y463`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/O75258.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["Q9Y463"]}, "queried": "O75258", "redirectedTo": "/uniprotkb/Q9Y463?from=O75258", "uniProtkbId": "O75258"} ; resolved to live entry Q9Y463 -> {"accession": "Q9Y463", "gene": {"name": "DYRK1B", "synonyms": ["MIRK"]}, "id": "DYR1B_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Dual specificity tyrosine-phosphorylation-regulated kinase 1B", "secondaryAccession": ["O75258", "O75788", "O75789"]}
  ```

- **why**: UniProt reports O75258 as MERGED into Q9Y463. Its content now lives under Q9Y463.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession Q9Y463 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 998 (O75258)`

---

### `obsolete_accession` — EPHA2 (medium)

- **observed** (in file): `B5A968`
- **correct** (per authority): `P29317`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/B5A968.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["P29317"]}, "queried": "B5A968", "redirectedTo": "/uniprotkb/P29317?from=B5A968", "uniProtkbId": "B5A968_HUMAN"} ; resolved to live entry P29317 -> {"accession": "P29317", "gene": {"name": "EPHA2", "synonyms": ["ECK"]}, "id": "EPHA2_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Ephrin type-A receptor 2", "secondaryAccession": ["B5A968", "Q8N3Z2"]}
  ```

- **why**: UniProt reports B5A968 as MERGED into P29317. Its content now lives under P29317.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession P29317 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (2): `source_chembl.csv row 81 (CHEMBL2068)`; `source_uniprot.csv row 551 (B5A968)`

---

### `obsolete_accession` — EZH2 (medium)

- **observed** (in file): `B2RAQ1`
- **correct** (per authority): `Q15910`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/B2RAQ1.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["Q15910"]}, "queried": "B2RAQ1", "redirectedTo": "/uniprotkb/Q15910?from=B2RAQ1", "uniProtkbId": "B2RAQ1_HUMAN"} ; resolved to live entry Q15910 -> {"accession": "Q15910", "gene": {"name": "EZH2", "synonyms": ["KMT6"]}, "id": "EZH2_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Histone-lysine N-methyltransferase EZH2", "secondaryAccession": ["B2RAQ1", "B3KS30", "B7Z1D6", "B7Z7L6", "Q15755", "Q75MG3", "Q92857", "Q96FI6"]}
  ```

- **why**: UniProt reports B2RAQ1 as MERGED into Q15910. Its content now lives under Q15910.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession Q15910 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 733 (B2RAQ1)`

---

### `obsolete_accession` — GALR1 (medium)

- **observed** (in file): `Q4VBL7`
- **correct** (per authority): `P47211`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/Q4VBL7.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["P47211"]}, "queried": "Q4VBL7", "redirectedTo": "/uniprotkb/P47211?from=Q4VBL7", "uniProtkbId": "Q4VBL7_HUMAN"} ; resolved to live entry P47211 -> {"accession": "P47211", "gene": {"name": "GALR1", "synonyms": ["GALNR", "GALNR1"]}, "id": "GALR1_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Galanin receptor type 1", "secondaryAccession": ["Q4VBL7"]}
  ```

- **why**: UniProt reports Q4VBL7 as MERGED into P47211. Its content now lives under P47211.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession P47211 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 299 (Q4VBL7)`

---

### `obsolete_accession` — HCRTR2 (medium)

- **observed** (in file): `Q5VTM0`
- **correct** (per authority): `O43614`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/Q5VTM0.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["O43614"]}, "queried": "Q5VTM0", "redirectedTo": "/uniprotkb/O43614?from=Q5VTM0", "uniProtkbId": "Q5VTM0_HUMAN"} ; resolved to live entry O43614 -> {"accession": "O43614", "gene": {"name": "HCRTR2", "synonyms": ["ORXR2", "OX2R", "OXR2"]}, "id": "OX2R_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Orexin receptor type 2", "secondaryAccession": ["Q5VTM0"]}
  ```

- **why**: UniProt reports Q5VTM0 as MERGED into O43614. Its content now lives under O43614.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession O43614 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 64 (Q5VTM0)`

---

### `obsolete_accession` — HDAC4 (medium)

- **observed** (in file): `E9PGB9`
- **correct** (per authority): `P56524`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/E9PGB9.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["Q86YH7"]}, "queried": "E9PGB9", "redirectedTo": "/uniprotkb/Q86YH7?from=E9PGB9", "uniProtkbId": "E9PGB9_HUMAN"} ; resolved to live entry P56524 -> {"accession": "P56524", "gene": {"name": "HDAC4", "synonyms": ["KIAA0288"]}, "id": "HDAC4_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Histone deacetylase 4", "secondaryAccession": ["E9PGB9", "F5GX36", "Q86YH7", "Q9UND6"]}
  ```

- **why**: UniProt reports E9PGB9 as MERGED into Q86YH7. Chain: E9PGB9 was MERGED into Q86YH7; Q86YH7 was MERGED into P56524. 
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession P56524 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 214 (E9PGB9)`

---

### `obsolete_accession` — HNF4A (medium)

- **observed** (in file): `A5JW41`
- **correct** (per authority): `P41235`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/A5JW41.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["P41235"]}, "queried": "A5JW41", "redirectedTo": "/uniprotkb/P41235?from=A5JW41", "uniProtkbId": "A5JW41_HUMAN"} ; resolved to live entry P41235 -> {"accession": "P41235", "gene": {"name": "HNF4A", "synonyms": ["HNF4", "NR2A1", "TCF14"]}, "id": "HNF4A_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Hepatocyte nuclear factor 4-alpha", "secondaryAccession": ["A5JW41", "B2RPP8", "O00659", "O00723", "Q14540", "Q5QPB8", "Q6B4V5", "Q6B4V6", "Q6B4V7", "Q92653", "Q92654", "Q92655", "Q99864", "Q9NQH0"]}
  ```

- **why**: UniProt reports A5JW41 as MERGED into P41235. Its content now lives under P41235.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession P41235 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_uniprot.csv row 384 (A5JW41)`

---

### `obsolete_accession` — HNF4A (medium)

- **observed** (in file): `B2RPP8`
- **correct** (per authority): `P41235`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/B2RPP8.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["P41235"]}, "queried": "B2RPP8", "redirectedTo": "/uniprotkb/P41235?from=B2RPP8", "uniProtkbId": "B2RPP8_HUMAN"} ; resolved to live entry P41235 -> {"accession": "P41235", "gene": {"name": "HNF4A", "synonyms": ["HNF4", "NR2A1", "TCF14"]}, "id": "HNF4A_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Hepatocyte nuclear factor 4-alpha", "secondaryAccession": ["A5JW41", "B2RPP8", "O00659", "O00723", "Q14540", "Q5QPB8", "Q6B4V5", "Q6B4V6", "Q6B4V7", "Q92653", "Q92654", "Q92655", "Q99864", "Q9NQH0"]}
  ```

- **why**: UniProt reports B2RPP8 as MERGED into P41235. Its content now lives under P41235.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession P41235 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_uniprot.csv row 192 (B2RPP8)`

---

### `obsolete_accession` — IFNA13 (medium)

- **observed** (in file): `D4Q9M8`
- **correct** (per authority): `A0A087WWS6`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/D4Q9M8.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["P01562"]}, "queried": "D4Q9M8", "redirectedTo": "/uniprotkb/P01562?from=D4Q9M8", "uniProtkbId": "D4Q9M8_HUMAN"} ; resolved to live entry A0A087WWS6 -> {"accession": "A0A087WWS6", "gene": {"name": "IFNA13", "synonyms": []}, "id": "IFNAD_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Interferon alpha-13", "secondaryAccession": ["D4Q9M8", "P01562", "Q14605", "Q2M1L8", "Q52LB8", "Q5VYQ2", "Q7M4Q1", "Q8WZ68", "Q9UMJ3"]}
  ```

- **why**: UniProt reports D4Q9M8 as MERGED into P01562. Chain: D4Q9M8 was MERGED into P01562; P01562 was DEMERGED into A0A087WWS6. 
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession A0A087WWS6 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_uniprot.csv row 387 (D4Q9M8)`

---

### `obsolete_accession` — IFNA13 (medium)

- **observed** (in file): `P01562`
- **correct** (per authority): `A0A087WWS6`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/P01562.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "DEMERGED", "mergeDemergeTo": ["A0A087WWS6", "P0DY56"]}, "queried": "P01562", "redirectedTo": "https://rest.uniprot.org/uniprotkb/P01562.json", "uniProtkbId": "IFNA1_HUMAN"} ; resolved to live entry A0A087WWS6 -> {"accession": "A0A087WWS6", "gene": {"name": "IFNA13", "synonyms": []}, "id": "IFNAD_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Interferon alpha-13", "secondaryAccession": ["D4Q9M8", "P01562", "Q14605", "Q2M1L8", "Q52LB8", "Q5VYQ2", "Q7M4Q1", "Q8WZ68", "Q9UMJ3"]}
  ```

- **why**: UniProt reports P01562 as DEMERGED into A0A087WWS6, P0DY56. The entry was demerged into A0A087WWS6, P0DY56; the row's own gene symbol IFNA13 matches A0A087WWS6 (approved symbol IFNA13), so that is the side of the split it denotes.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession A0A087WWS6 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_uniprot.csv row 381 (P01562)`

---

### `obsolete_accession` — MAP3K5 (medium)

- **observed** (in file): `A6NIA0`
- **correct** (per authority): `Q99683`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/A6NIA0.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["Q99683"]}, "queried": "A6NIA0", "redirectedTo": "/uniprotkb/Q99683?from=A6NIA0", "uniProtkbId": "A6NIA0_HUMAN"} ; resolved to live entry Q99683 -> {"accession": "Q99683", "gene": {"name": "MAP3K5", "synonyms": ["ASK1", "MAPKKK5", "MEKK5"]}, "id": "M3K5_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Mitogen-activated protein kinase kinase kinase 5", "secondaryAccession": ["A6NIA0", "B4DGB2", "Q5THN3", "Q99461"]}
  ```

- **why**: UniProt reports A6NIA0 as MERGED into Q99683. Its content now lives under Q99683.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession Q99683 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 518 (A6NIA0)`

---

### `obsolete_accession` — MAPK10 (medium)

- **observed** (in file): `A6NFS3`
- **correct** (per authority): `P53779`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/A6NFS3.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["P53779"]}, "queried": "A6NFS3", "redirectedTo": "/uniprotkb/P53779?from=A6NFS3", "uniProtkbId": "A6NFS3_HUMAN"} ; resolved to live entry P53779 -> {"accession": "P53779", "gene": {"name": "MAPK10", "synonyms": ["JNK3", "JNK3A", "PRKM10", "SAPK1B"]}, "id": "MK10_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Mitogen-activated protein kinase 10", "secondaryAccession": ["A6NFS3", "A6NG28", "B3KQ94", "Q15707", "Q49AP1"]}
  ```

- **why**: UniProt reports A6NFS3 as MERGED into P53779. Its content now lives under P53779.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession P53779 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 290 (A6NFS3)`

---

### `obsolete_accession` — MAPK11 (medium)

- **observed** (in file): `A8K730`
- **correct** (per authority): `Q15759`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/A8K730.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["Q15759"]}, "queried": "A8K730", "redirectedTo": "/uniprotkb/Q15759?from=A8K730", "uniProtkbId": "A8K730_HUMAN"} ; resolved to live entry Q15759 -> {"accession": "Q15759", "gene": {"name": "MAPK11", "synonyms": ["PRKM11", "SAPK2", "SAPK2B"]}, "id": "MK11_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Mitogen-activated protein kinase 11", "secondaryAccession": ["A8K730", "B0LPG1", "B7Z630", "E7ETQ1", "L7RT27", "O00284", "O15472", "Q2XNF2"]}
  ```

- **why**: UniProt reports A8K730 as MERGED into Q15759. Its content now lives under Q15759.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession Q15759 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 158 (A8K730)`

---

### `obsolete_accession` — NMUR2 (medium)

- **observed** (in file): `Q7LC54`
- **correct** (per authority): `Q9GZQ4`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/Q7LC54.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["Q9GZQ4"]}, "queried": "Q7LC54", "redirectedTo": "/uniprotkb/Q9GZQ4?from=Q7LC54", "uniProtkbId": "Q7LC54_HUMAN"} ; resolved to live entry Q9GZQ4 -> {"accession": "Q9GZQ4", "gene": {"name": "NMUR2", "synonyms": ["NMU2", "NMU2R", "TGR1"]}, "id": "NMUR2_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Neuromedin-U receptor 2", "secondaryAccession": ["Q7LC54", "Q96AM5", "Q9NRA6"]}
  ```

- **why**: UniProt reports Q7LC54 as MERGED into Q9GZQ4. Its content now lives under Q9GZQ4.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession Q9GZQ4 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 568 (Q7LC54)`

---

### `obsolete_accession` — NR4A1 (medium)

- **observed** (in file): `B4DML7`
- **correct** (per authority): `P22736`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/B4DML7.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["P22736"]}, "queried": "B4DML7", "redirectedTo": "/uniprotkb/P22736?from=B4DML7", "uniProtkbId": "B4DML7_HUMAN"} ; resolved to live entry P22736 -> {"accession": "P22736", "gene": {"name": "NR4A1", "synonyms": ["GFRP1", "HMR", "NAK1"]}, "id": "NR4A1_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Nuclear receptor subfamily 4immunitygroup A member 1", "secondaryAccession": ["B4DML7", "Q15627", "Q53Y00", "Q6IBU8"]}
  ```

- **why**: UniProt reports B4DML7 as MERGED into P22736. Its content now lives under P22736.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession P22736 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 411 (B4DML7)`

---

### `obsolete_accession` — PLK4 (medium)

- **observed** (in file): `B2RAL0`
- **correct** (per authority): `O00444`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/B2RAL0.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["O00444"]}, "queried": "B2RAL0", "redirectedTo": "/uniprotkb/O00444?from=B2RAL0", "uniProtkbId": "B2RAL0_HUMAN"} ; resolved to live entry O00444 -> {"accession": "O00444", "gene": {"name": "PLK4", "synonyms": ["SAK", "STK18"]}, "id": "PLK4_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Serine/threonine-protein kinase PLK4", "secondaryAccession": ["B2RAL0", "B7Z837", "B7Z8G7", "Q8IYF0", "Q96Q95", "Q9UD84", "Q9UDE2"]}
  ```

- **why**: UniProt reports B2RAL0 as MERGED into O00444. Its content now lives under O00444.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession O00444 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 893 (B2RAL0)`

---

### `obsolete_accession` — RIPK3 (medium)

- **observed** (in file): `B4DJL9`
- **correct** (per authority): `Q9Y572`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/B4DJL9.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["Q9Y572"]}, "queried": "B4DJL9", "redirectedTo": "/uniprotkb/Q9Y572?from=B4DJL9", "uniProtkbId": "B4DJL9_HUMAN"} ; resolved to live entry Q9Y572 -> {"accession": "Q9Y572", "gene": {"name": "RIPK3", "synonyms": ["RIP3"]}, "id": "RIPK3_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Receptor-interacting serine/threonine-protein kinase 3", "secondaryAccession": ["B4DJL9", "C4AM87", "Q5J795", "Q5J796", "Q6P5Y1"]}
  ```

- **why**: UniProt reports B4DJL9 as MERGED into Q9Y572. Its content now lives under Q9Y572.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession Q9Y572 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 631 (B4DJL9)`

---

### `obsolete_accession` — SRPK1 (medium)

- **observed** (in file): `B4DS61`
- **correct** (per authority): `Q96SB4`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/B4DS61.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["Q96SB4"]}, "queried": "B4DS61", "redirectedTo": "/uniprotkb/Q96SB4?from=B4DS61", "uniProtkbId": "B4DS61_HUMAN"} ; resolved to live entry Q96SB4 -> {"accession": "Q96SB4", "gene": {"name": "SRPK1", "synonyms": []}, "id": "SRPK1_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "SRSF protein kinase 1", "secondaryAccession": ["B4DS61", "Q12890", "Q5R364", "Q5R365", "Q8IY12"]}
  ```

- **why**: UniProt reports B4DS61 as MERGED into Q96SB4. Its content now lives under Q96SB4.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession Q96SB4 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (2): `source_chembl.csv row 293 (CHEMBL4375)`; `source_uniprot.csv row 163 (B4DS61)`

---

### `obsolete_accession` — TBK1 (medium)

- **observed** (in file): `A8K4S4`
- **correct** (per authority): `Q9UHD2`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/A8K4S4.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["Q9UHD2"]}, "queried": "A8K4S4", "redirectedTo": "/uniprotkb/Q9UHD2?from=A8K4S4", "uniProtkbId": "A8K4S4_HUMAN"} ; resolved to live entry Q9UHD2 -> {"accession": "Q9UHD2", "gene": {"name": "TBK1", "synonyms": ["NAK"]}, "id": "TBK1_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Serine/threonine-protein kinase TBK1", "secondaryAccession": ["A8K4S4", "Q8IYV3", "Q9NUJ5"]}
  ```

- **why**: UniProt reports A8K4S4 as MERGED into Q9UHD2. Its content now lives under Q9UHD2.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession Q9UHD2 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 489 (A8K4S4)`

---

### `obsolete_accession` — THRB (medium)

- **observed** (in file): `B3KU79`
- **correct** (per authority): `P10828`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/B3KU79.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["P10828"]}, "queried": "B3KU79", "redirectedTo": "/uniprotkb/P10828?from=B3KU79", "uniProtkbId": "B3KU79_HUMAN"} ; resolved to live entry P10828 -> {"accession": "P10828", "gene": {"name": "THRB", "synonyms": ["ERBA2", "NR1A2", "THR1"]}, "id": "THB_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Thyroid hormone receptor beta", "secondaryAccession": ["B3KU79", "P37243", "Q13986", "Q3KP35", "Q6WGL2", "Q9UD41"]}
  ```

- **why**: UniProt reports B3KU79 as MERGED into P10828. Its content now lives under P10828.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession P10828 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 629 (B3KU79)`

---

### `obsolete_accession` — USP7 (medium)

- **observed** (in file): `A6NMY8`
- **correct** (per authority): `Q93009`
- **field**: `accession`
- **evidence_source**: `UniProt REST GET /uniprotkb/A6NMY8.json`
- **retrieved_evidence**:

  ```
  {"entryType": "Inactive", "inactiveReason": {"inactiveReasonType": "MERGED", "mergeDemergeTo": ["Q93009"]}, "queried": "A6NMY8", "redirectedTo": "/uniprotkb/Q93009?from=A6NMY8", "uniProtkbId": "A6NMY8_HUMAN"} ; resolved to live entry Q93009 -> {"accession": "Q93009", "gene": {"name": "USP7", "synonyms": ["HAUSP"]}, "id": "UBP7_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Ubiquitin C-terminal hydrolase 7", "secondaryAccession": ["A6NMY8", "B7Z815", "H0Y3G8"]}
  ```

- **why**: UniProt reports A6NMY8 as MERGED into Q93009. Its content now lives under Q93009.
- **impact**: Dead key: the row survives as a phantom target and splits one real entity across two master records. The successor accession Q93009 is also present in this pack, so the two together form a duplicate identity for one protein.
- **rows** (1): `source_bindingdb.csv row 1079 (A6NMY8)`

---

### `wrong_crossreference` — PDE10A (medium)

- **observed** (in file): `CHEMBL3012`
- **correct** (per authority): `CHEMBL4409`
- **field**: `chembl_id`
- **evidence_source**: `UniProt REST GET /uniprotkb/search?query=xref:chembl-CHEMBL3012`
- **retrieved_evidence**:

  ```
  {"accession": "Q9Y233", "gene": {"name": "PDE10A", "synonyms": []}, "id": "PDE10_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "cAMP and cAMP-inhibited cGMP 3',5'-cyclic phosphodiesterase 10A", "secondaryAccession": ["A0A3F2YP58", "Q6FHX1", "Q9HCP9", "Q9NTV4", "Q9ULW9", "Q9Y5T1"]} ; UniProt lists ChEMBL cross-reference(s) CHEMBL4409 for Q9Y233, while CHEMBL3012 belongs to Q13946 (PDE7A_HUMAN)
  ```

- **why**: The row describes Q9Y233 (PDE10A, confirmed by its own gene symbol), but carries ChEMBL id CHEMBL3012, which UniProt cross-references to Q13946 (PDE7A_HUMAN). The correct ChEMBL id for this target is CHEMBL4409.
- **impact**: Broken join: downstream lookups by ChEMBL id retrieve a different target.
- **rows** (1): `source_chembl.csv row 254 (CHEMBL3012)`

---

### `ambiguous_mention` — KLK3 (medium)

- **observed** (in file): `PSA`
- **correct** (per authority): `KLK3`
- **field**: `target_mention`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P07288`
- **retrieved_evidence**:

  ```
  {"accession": "P07288", "gene": {"name": "KLK3", "synonyms": ["APS"]}, "id": "KLK3_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Prostate-specific antigen", "secondaryAccession": ["C9JXH3", "G3V0H4", "G3XAE3", "Q15096", "Q16272", "Q86TG8", "Q8IXI4"]} ; alias 'PSA' is shared by P07288=KLK3, P55786=NPEPPS, and the authority's description of P07288 matches the context sentence on glycoprotein
  ```

- **why**: 'PSA' is not the approved symbol of a single target: the authority shows it is shared by KLK3 (P07288) and NPEPPS (P55786). The context sentence 'Serum levels of the glycoprotein guided biopsy decisions in the population screening cohort.' describes KLK3 (P07288, Prostate-specific antigen), so this mention resolves to KLK3.
- **impact**: Ambiguous mention: attributing this publication to the wrong gene mis-assigns literature evidence between two unrelated proteins.
- **rows** (5): `source_publications.csv row 276 (30010616)`; `source_publications.csv row 332 (30041117)`; `source_publications.csv row 359 (30082617)`; `source_publications.csv row 497 (30099162)`; `source_publications.csv row 624 (30067416)`

---

### `ambiguous_mention` — NPEPPS (medium)

- **observed** (in file): `PSA`
- **correct** (per authority): `NPEPPS`
- **field**: `target_mention`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P55786`
- **retrieved_evidence**:

  ```
  {"accession": "P55786", "gene": {"name": "NPEPPS", "synonyms": ["PSA"]}, "id": "PSA_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Puromycin-sensitive aminopeptidase", "secondaryAccession": ["B7Z463", "Q6P145", "Q9NP16", "Q9UEM2"]} ; alias 'PSA' is shared by P55786=NPEPPS, P07288=KLK3, and the authority's description of P55786 matches the context sentence on aminopeptidase, cytosolic, tau, zinc
  ```

- **why**: 'PSA' is not the approved symbol of a single target: the authority shows it is shared by NPEPPS (P55786) and KLK3 (P07288). The context sentence 'The cytosolic zinc aminopeptidase degraded tau and mitigated neurofibrillary pathology in transgenic models.' describes NPEPPS (P55786, Puromycin-sensitive aminopeptidase), so this mention resolves to NPEPPS.
- **impact**: Ambiguous mention: attributing this publication to the wrong gene mis-assigns literature evidence between two unrelated proteins.
- **rows** (2): `source_publications.csv row 219 (30087819)`; `source_publications.csv row 45 (30072062)`

---

### `stale_gene_symbol` — ADAM17 (low)

- **observed** (in file): `CSVP`
- **correct** (per authority): `ADAM17`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P78536`
- **retrieved_evidence**:

  ```
  {"accession": "P78536", "gene": {"name": "ADAM17", "synonyms": ["CSVP", "TACE"]}, "id": "ADA17_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Disintegrin and metalloproteinase domain-containing protein 17", "secondaryAccession": ["O60226"]}
  ```

- **why**: CSVP is listed by the authority as a synonym of ADAM17 (entry ADA17_HUMAN), not its approved symbol. The accession O60226 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 52 (O60226)`

---

### `stale_gene_symbol` — ADRA2A (low)

- **observed** (in file): `ADRA2R`
- **correct** (per authority): `ADRA2A`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P08913`
- **retrieved_evidence**:

  ```
  {"accession": "P08913", "gene": {"name": "ADRA2A", "synonyms": ["ADRA2R", "ADRAR"]}, "id": "ADA2A_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Alpha-2A adrenergic receptor", "secondaryAccession": ["B0LPF6", "Q2I8G2", "Q2XN99", "Q86TH8", "Q9BZK1"]}
  ```

- **why**: ADRA2R is listed by the authority as a synonym of ADRA2A (entry ADA2A_HUMAN), not its approved symbol. The accession B0LPF6 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 492 (B0LPF6)`

---

### `stale_gene_symbol` — AXL (low)

- **observed** (in file): `UFO`
- **correct** (per authority): `AXL`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P30530`
- **retrieved_evidence**:

  ```
  {"accession": "P30530", "gene": {"name": "AXL", "synonyms": ["UFO"]}, "id": "UFO_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Tyrosine-protein kinase receptor UFO", "secondaryAccession": ["Q8N5L2", "Q9UD27"]}
  ```

- **why**: UFO is listed by the authority as a synonym of AXL (entry UFO_HUMAN), not its approved symbol. The accession Q8N5L2 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 146 (Q8N5L2)`

---

### `stale_gene_symbol` — BRD2 (low)

- **observed** (in file): `KIAA9001`
- **correct** (per authority): `BRD2`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P25440`
- **retrieved_evidence**:

  ```
  {"accession": "P25440", "gene": {"name": "BRD2", "synonyms": ["KIAA9001", "RING3"]}, "id": "BRD2_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Bromodomain-containing protein 2", "secondaryAccession": ["A2AAU0", "B0S7P0", "B1AZT1", "O00699", "O00700", "Q15310", "Q5STC9", "Q63HQ9", "Q658Y7", "Q6P3U2", "Q969U4"]}
  ```

- **why**: KIAA9001 is listed by the authority as a synonym of BRD2 (entry BRD2_HUMAN), not its approved symbol. The accession A2AAU0 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 1127 (A2AAU0)`

---

### `stale_gene_symbol` — CA9 (low)

- **observed** (in file): `G250`
- **correct** (per authority): `CA9`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=Q16790`
- **retrieved_evidence**:

  ```
  {"accession": "Q16790", "gene": {"name": "CA9", "synonyms": ["G250", "MN"]}, "id": "CAH9_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Carbonic anhydrase 9", "secondaryAccession": ["Q5T4R1"]}
  ```

- **why**: G250 is listed by the authority as a synonym of CA9 (entry CAH9_HUMAN), not its approved symbol. The accession Q5T4R1 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 364 (Q5T4R1)`

---

### `stale_gene_symbol` — DYRK1B (low)

- **observed** (in file): `MIRK`
- **correct** (per authority): `DYRK1B`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=Q9Y463`
- **retrieved_evidence**:

  ```
  {"accession": "Q9Y463", "gene": {"name": "DYRK1B", "synonyms": ["MIRK"]}, "id": "DYR1B_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Dual specificity tyrosine-phosphorylation-regulated kinase 1B", "secondaryAccession": ["O75258", "O75788", "O75789"]}
  ```

- **why**: MIRK is listed by the authority as a synonym of DYRK1B (entry DYR1B_HUMAN), not its approved symbol. The accession O75258 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 998 (O75258)`

---

### `stale_gene_symbol` — EZH2 (low)

- **observed** (in file): `KMT6`
- **correct** (per authority): `EZH2`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=Q15910`
- **retrieved_evidence**:

  ```
  {"accession": "Q15910", "gene": {"name": "EZH2", "synonyms": ["KMT6"]}, "id": "EZH2_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Histone-lysine N-methyltransferase EZH2", "secondaryAccession": ["B2RAQ1", "B3KS30", "B7Z1D6", "B7Z7L6", "Q15755", "Q75MG3", "Q92857", "Q96FI6"]}
  ```

- **why**: KMT6 is listed by the authority as a synonym of EZH2 (entry EZH2_HUMAN), not its approved symbol. The accession B2RAQ1 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 733 (B2RAQ1)`

---

### `stale_gene_symbol` — GALR1 (low)

- **observed** (in file): `GALNR`
- **correct** (per authority): `GALR1`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P47211`
- **retrieved_evidence**:

  ```
  {"accession": "P47211", "gene": {"name": "GALR1", "synonyms": ["GALNR", "GALNR1"]}, "id": "GALR1_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Galanin receptor type 1", "secondaryAccession": ["Q4VBL7"]}
  ```

- **why**: GALNR is listed by the authority as a synonym of GALR1 (entry GALR1_HUMAN), not its approved symbol. The accession Q4VBL7 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 299 (Q4VBL7)`

---

### `stale_gene_symbol` — HCRTR2 (low)

- **observed** (in file): `ORXR2`
- **correct** (per authority): `HCRTR2`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=O43614`
- **retrieved_evidence**:

  ```
  {"accession": "O43614", "gene": {"name": "HCRTR2", "synonyms": ["ORXR2", "OX2R", "OXR2"]}, "id": "OX2R_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Orexin receptor type 2", "secondaryAccession": ["Q5VTM0"]}
  ```

- **why**: ORXR2 is listed by the authority as a synonym of HCRTR2 (entry OX2R_HUMAN), not its approved symbol. The accession Q5VTM0 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 64 (Q5VTM0)`

---

### `stale_gene_symbol` — HDAC4 (low)

- **observed** (in file): `KIAA0288`
- **correct** (per authority): `HDAC4`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P56524`
- **retrieved_evidence**:

  ```
  {"accession": "P56524", "gene": {"name": "HDAC4", "synonyms": ["KIAA0288"]}, "id": "HDAC4_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Histone deacetylase 4", "secondaryAccession": ["E9PGB9", "F5GX36", "Q86YH7", "Q9UND6"]}
  ```

- **why**: KIAA0288 is listed by the authority as a synonym of HDAC4 (entry HDAC4_HUMAN), not its approved symbol. The accession E9PGB9 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 214 (E9PGB9)`

---

### `stale_gene_symbol` — MAP3K5 (low)

- **observed** (in file): `ASK1`
- **correct** (per authority): `MAP3K5`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=Q99683`
- **retrieved_evidence**:

  ```
  {"accession": "Q99683", "gene": {"name": "MAP3K5", "synonyms": ["ASK1", "MAPKKK5", "MEKK5"]}, "id": "M3K5_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Mitogen-activated protein kinase kinase kinase 5", "secondaryAccession": ["A6NIA0", "B4DGB2", "Q5THN3", "Q99461"]}
  ```

- **why**: ASK1 is listed by the authority as a synonym of MAP3K5 (entry M3K5_HUMAN), not its approved symbol. The accession A6NIA0 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 518 (A6NIA0)`

---

### `stale_gene_symbol` — MAPK10 (low)

- **observed** (in file): `JNK3`
- **correct** (per authority): `MAPK10`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P53779`
- **retrieved_evidence**:

  ```
  {"accession": "P53779", "gene": {"name": "MAPK10", "synonyms": ["JNK3", "JNK3A", "PRKM10", "SAPK1B"]}, "id": "MK10_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Mitogen-activated protein kinase 10", "secondaryAccession": ["A6NFS3", "A6NG28", "B3KQ94", "Q15707", "Q49AP1"]}
  ```

- **why**: JNK3 is listed by the authority as a synonym of MAPK10 (entry MK10_HUMAN), not its approved symbol. The accession A6NFS3 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 290 (A6NFS3)`

---

### `stale_gene_symbol` — MAPK11 (low)

- **observed** (in file): `PRKM11`
- **correct** (per authority): `MAPK11`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=Q15759`
- **retrieved_evidence**:

  ```
  {"accession": "Q15759", "gene": {"name": "MAPK11", "synonyms": ["PRKM11", "SAPK2", "SAPK2B"]}, "id": "MK11_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Mitogen-activated protein kinase 11", "secondaryAccession": ["A8K730", "B0LPG1", "B7Z630", "E7ETQ1", "L7RT27", "O00284", "O15472", "Q2XNF2"]}
  ```

- **why**: PRKM11 is listed by the authority as a synonym of MAPK11 (entry MK11_HUMAN), not its approved symbol. The accession A8K730 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 158 (A8K730)`

---

### `stale_gene_symbol` — NMUR2 (low)

- **observed** (in file): `NMU2`
- **correct** (per authority): `NMUR2`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=Q9GZQ4`
- **retrieved_evidence**:

  ```
  {"accession": "Q9GZQ4", "gene": {"name": "NMUR2", "synonyms": ["NMU2", "NMU2R", "TGR1"]}, "id": "NMUR2_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Neuromedin-U receptor 2", "secondaryAccession": ["Q7LC54", "Q96AM5", "Q9NRA6"]}
  ```

- **why**: NMU2 is listed by the authority as a synonym of NMUR2 (entry NMUR2_HUMAN), not its approved symbol. The accession Q7LC54 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 568 (Q7LC54)`

---

### `stale_gene_symbol` — NR4A1 (low)

- **observed** (in file): `GFRP1`
- **correct** (per authority): `NR4A1`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P22736`
- **retrieved_evidence**:

  ```
  {"accession": "P22736", "gene": {"name": "NR4A1", "synonyms": ["GFRP1", "HMR", "NAK1"]}, "id": "NR4A1_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Nuclear receptor subfamily 4immunitygroup A member 1", "secondaryAccession": ["B4DML7", "Q15627", "Q53Y00", "Q6IBU8"]}
  ```

- **why**: GFRP1 is listed by the authority as a synonym of NR4A1 (entry NR4A1_HUMAN), not its approved symbol. The accession B4DML7 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 411 (B4DML7)`

---

### `stale_gene_symbol` — NSD2 (low)

- **observed** (in file): `WHSC1`
- **correct** (per authority): `NSD2`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=O96028`
- **retrieved_evidence**:

  ```
  {"accession": "O96028", "gene": {"name": "NSD2", "synonyms": ["KIAA1090", "MMSET", "TRX5", "WHSC1"]}, "id": "NSD2_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Histone-lysine N-methyltransferase NSD2", "secondaryAccession": ["A2A2T2", "A2A2T3", "A2A2T4", "A7MCZ1", "D3DVQ2", "O96031", "Q4VBY8", "Q672J1", "Q6IS00", "Q86V01", "Q9BZB4", "Q9UI92", "Q9UPR2"]}
  ```

- **why**: WHSC1 is listed by the authority as a synonym of NSD2 (entry NSD2_HUMAN), not its approved symbol. The accession O96028 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_internal.csv row 92 (TGT-2425)`

---

### `stale_gene_symbol` — PLK4 (low)

- **observed** (in file): `SAK`
- **correct** (per authority): `PLK4`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=O00444`
- **retrieved_evidence**:

  ```
  {"accession": "O00444", "gene": {"name": "PLK4", "synonyms": ["SAK", "STK18"]}, "id": "PLK4_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Serine/threonine-protein kinase PLK4", "secondaryAccession": ["B2RAL0", "B7Z837", "B7Z8G7", "Q8IYF0", "Q96Q95", "Q9UD84", "Q9UDE2"]}
  ```

- **why**: SAK is listed by the authority as a synonym of PLK4 (entry PLK4_HUMAN), not its approved symbol. The accession B2RAL0 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 893 (B2RAL0)`

---

### `stale_gene_symbol` — RIPK3 (low)

- **observed** (in file): `RIP3`
- **correct** (per authority): `RIPK3`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=Q9Y572`
- **retrieved_evidence**:

  ```
  {"accession": "Q9Y572", "gene": {"name": "RIPK3", "synonyms": ["RIP3"]}, "id": "RIPK3_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Receptor-interacting serine/threonine-protein kinase 3", "secondaryAccession": ["B4DJL9", "C4AM87", "Q5J795", "Q5J796", "Q6P5Y1"]}
  ```

- **why**: RIP3 is listed by the authority as a synonym of RIPK3 (entry RIPK3_HUMAN), not its approved symbol. The accession B4DJL9 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 631 (B4DJL9)`

---

### `stale_gene_symbol` — SEPTIN9 (low)

- **observed** (in file): `SEPT9`
- **correct** (per authority): `SEPTIN9`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=Q9UHD8`
- **retrieved_evidence**:

  ```
  {"accession": "Q9UHD8", "gene": {"name": "SEPTIN9", "synonyms": ["KIAA0991", "MSF", "SEPT9"]}, "id": "SEPT9_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Septin-9", "secondaryAccession": ["A8K2V3", "B3KPM0", "B4DTL9", "B4E0N2", "B4E274", "B7Z654", "Q96QF3", "Q96QF4", "Q96QF5", "Q9HA04", "Q9UG40", "Q9Y5W4"]}
  ```

- **why**: SEPT9 is listed by the authority as a synonym of SEPTIN9 (entry SEPT9_HUMAN), not its approved symbol. The accession Q9UHD8 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_internal.csv row 8 (TGT-2433)`

---

### `stale_gene_symbol` — TBK1 (low)

- **observed** (in file): `NAK`
- **correct** (per authority): `TBK1`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=Q9UHD2`
- **retrieved_evidence**:

  ```
  {"accession": "Q9UHD2", "gene": {"name": "TBK1", "synonyms": ["NAK"]}, "id": "TBK1_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Serine/threonine-protein kinase TBK1", "secondaryAccession": ["A8K4S4", "Q8IYV3", "Q9NUJ5"]}
  ```

- **why**: NAK is listed by the authority as a synonym of TBK1 (entry TBK1_HUMAN), not its approved symbol. The accession A8K4S4 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 489 (A8K4S4)`

---

### `stale_gene_symbol` — THRB (low)

- **observed** (in file): `ERBA2`
- **correct** (per authority): `THRB`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P10828`
- **retrieved_evidence**:

  ```
  {"accession": "P10828", "gene": {"name": "THRB", "synonyms": ["ERBA2", "NR1A2", "THR1"]}, "id": "THB_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Thyroid hormone receptor beta", "secondaryAccession": ["B3KU79", "P37243", "Q13986", "Q3KP35", "Q6WGL2", "Q9UD41"]}
  ```

- **why**: ERBA2 is listed by the authority as a synonym of THRB (entry THB_HUMAN), not its approved symbol. The accession B3KU79 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 629 (B3KU79)`

---

### `stale_gene_symbol` — USP7 (low)

- **observed** (in file): `HAUSP`
- **correct** (per authority): `USP7`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=Q93009`
- **retrieved_evidence**:

  ```
  {"accession": "Q93009", "gene": {"name": "USP7", "synonyms": ["HAUSP"]}, "id": "UBP7_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Ubiquitin C-terminal hydrolase 7", "secondaryAccession": ["A6NMY8", "B7Z815", "H0Y3G8"]}
  ```

- **why**: HAUSP is listed by the authority as a synonym of USP7 (entry UBP7_HUMAN), not its approved symbol. The accession A6NMY8 is correct, so this is a stale label rather than a wrong mapping.
- **impact**: Stale-but-valid label: harmless to a human, but defeats exact-symbol joins.
- **rows** (1): `source_bindingdb.csv row 1079 (A6NMY8)`

---

### `missing_gene_symbol` — HGS (low)

- **observed** (in file): `(empty gene_symbol)`
- **correct** (per authority): `HGS`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=O14964`
- **retrieved_evidence**:

  ```
  {"accession": "O14964", "gene": {"name": "HGS", "synonyms": ["HRS"]}, "id": "HGS_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Hepatocyte growth factor-regulated tyrosine kinase substrate", "secondaryAccession": ["Q9NR36"]}
  ```

- **why**: The row registers accession O14964 with no gene symbol. The authority gives the approved symbol as HGS (entry HGS_HUMAN).
- **impact**: Incomplete record: the golden record cannot be keyed by gene until this is filled.
- **rows** (2): `source_bindingdb.csv row 343 (O14964)`; `source_internal.csv row 164 (TGT-9369)`

---

### `missing_gene_symbol` — IGLV11-55 (low)

- **observed** (in file): `(empty gene_symbol)`
- **correct** (per authority): `IGLV11-55`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=A0A075B6I3`
- **retrieved_evidence**:

  ```
  {"accession": "A0A075B6I3", "gene": {"name": "IGLV11-55", "synonyms": []}, "id": "LVK55_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Probable non-functional immunoglobulin lambda variable 11-55", "secondaryAccession": []}
  ```

- **why**: The row registers accession A0A075B6I3 with no gene symbol. The authority gives the approved symbol as IGLV11-55 (entry LVK55_HUMAN).
- **impact**: Incomplete record: the golden record cannot be keyed by gene until this is filled.
- **rows** (2): `source_bindingdb.csv row 562 (A0A075B6I3)`; `source_internal.csv row 232 (TGT-9751)`

---

### `missing_gene_symbol` — IL1B (low)

- **observed** (in file): `(empty gene_symbol)`
- **correct** (per authority): `IL1B`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P01584`
- **retrieved_evidence**:

  ```
  {"accession": "P01584", "gene": {"name": "IL1B", "synonyms": ["IL1F2"]}, "id": "IL1B_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Interleukin-1 beta", "secondaryAccession": ["Q53X59", "Q53XX2", "Q7M4S7", "Q7RU01", "Q96HE5", "Q9UCT6"]}
  ```

- **why**: The row registers accession P01584 with no gene symbol. The authority gives the approved symbol as IL1B (entry IL1B_HUMAN).
- **impact**: Incomplete record: the golden record cannot be keyed by gene until this is filled.
- **rows** (2): `source_bindingdb.csv row 306 (P01584)`; `source_internal.csv row 155 (TGT-9855)`

---

### `missing_gene_symbol` — S100A4 (low)

- **observed** (in file): `(empty gene_symbol)`
- **correct** (per authority): `S100A4`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P26447`
- **retrieved_evidence**:

  ```
  {"accession": "P26447", "gene": {"name": "S100A4", "synonyms": ["CAPL", "MTS1"]}, "id": "S10A4_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "Protein S100-A4", "secondaryAccession": ["A8K7R8", "D3DV46", "Q6ICP8"]}
  ```

- **why**: The row registers accession P26447 with no gene symbol. The authority gives the approved symbol as S100A4 (entry S10A4_HUMAN).
- **impact**: Incomplete record: the golden record cannot be keyed by gene until this is filled.
- **rows** (2): `source_bindingdb.csv row 1107 (P26447)`; `source_internal.csv row 142 (TGT-9061)`

---

### `missing_gene_symbol` — SRGAP2C (low)

- **observed** (in file): `(empty gene_symbol)`
- **correct** (per authority): `SRGAP2C`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P0DJJ0`
- **retrieved_evidence**:

  ```
  {"accession": "P0DJJ0", "gene": {"name": "SRGAP2C", "synonyms": ["SRGAP2P1"]}, "id": "SRG2C_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "SLIT-ROBO Rho GTPase-activating protein 2C", "secondaryAccession": []}
  ```

- **why**: The row registers accession P0DJJ0 with no gene symbol. The authority gives the approved symbol as SRGAP2C (entry SRG2C_HUMAN).
- **impact**: Incomplete record: the golden record cannot be keyed by gene until this is filled.
- **rows** (2): `source_bindingdb.csv row 109 (P0DJJ0)`; `source_internal.csv row 216 (TGT-9328)`

---

### `missing_gene_symbol` — VIP (low)

- **observed** (in file): `(empty gene_symbol)`
- **correct** (per authority): `VIP`
- **field**: `gene_symbol`
- **evidence_source**: `EBI Proteins API GET /proteins?accession=P01282`
- **retrieved_evidence**:

  ```
  {"accession": "P01282", "gene": {"name": "VIP", "synonyms": []}, "id": "VIP_HUMAN", "organism": {"names": ["Homo sapiens", "Human"], "taxonomy": "9606"}, "recommendedName": "VIP peptides", "secondaryAccession": ["Q5TCY8", "Q5TCY9", "Q96QK3"]}
  ```

- **why**: The row registers accession P01282 with no gene symbol. The authority gives the approved symbol as VIP (entry VIP_HUMAN).
- **impact**: Incomplete record: the golden record cannot be keyed by gene until this is filled.
- **rows** (2): `source_bindingdb.csv row 208 (P01282)`; `source_internal.csv row 75 (TGT-9529)`
