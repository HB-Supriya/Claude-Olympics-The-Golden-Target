# Drug Discovery — Domain Primer

Background reading for the third Claude Olympics challenge (domain: **Drug Discovery**). No
problem statement or data has been shared yet — this file is pure domain-familiarization, built
from the public resources the user linked plus two Lilly-internal documents
(`Discovery onboarding June2024v2 (1).pptx`, `BRIDGE 2021 Q2 Seminar - Big Picture Drug
Discovery.pdf`, both living alongside this primer at the parent workspace level).
Written the same way as [[forecasting-challenge-playbook]] before the RetailCast challenge started
— read once for orientation, then treat it as a reference to come back to once the real
problem statement lands.

---

## 0. What the reading list itself implies (read this first)

The resource mix is a signal, not just background:
- Four resources are pure **biology/chemistry domain** (biological target, drug discovery process,
  genes, and the science side of UniProt/ChEMBL/BindingDB).
- Three resources are pure **data/enterprise-systems** topics that have nothing to do with biology
  per se: **UniProt/ChEMBL/BindingDB as databases** (schemas, identifiers, curation), **Master Data
  Management**, and **Data Quality**.

Pairing "what is a biological target" with "what is master data management" and "what is data
quality" strongly suggests the challenge is not a pure wet-lab-science or pure-ML-modeling task —
it's plausibly a **data curation / entity-resolution / data-quality problem set on top of
target–compound–assay reference data** (e.g., reconciling the same protein target or compound
across UniProt/ChEMBL/BindingDB-style identifiers, spotting duplicate/conflicting bioactivity
records, building a "golden record" for a target or compound, or scoring/cleaning a messy dataset
shaped like ChEMBL/BindingDB extracts). Treat this as a working hypothesis, not a certainty — but
it should shape what to practice: **schema/identifier reasoning and data-quality judgment on
biological reference data**, not just "learn pharmacology."

Everything below is organized so that hypothesis is easy to act on: science vocabulary first (§1–3),
then the actual data resources and their schemas (§4–6), then the MDM/data-quality lens to apply to
them (§7–8), then Lilly-specific organizational context (§9–10) in case the challenge is framed
around a specific stage of Lilly's own pipeline.

---

## 1. The drug discovery pipeline, end to end

High-level path (Wikipedia + Lilly's own pipeline diagram, terms aligned):

```
Target ID & Validation → Hit Generation (HTS/screening) → Hit-to-Lead → Lead Optimization →
Candidate Selection → Preclinical (Tox/ADME/PK-PD) → First Human Dose (FHD) / Phase I →
Phase II → Phase III → Registration/Submission → Launch → Post-launch (Phase IV)
```

- **Target identification & validation**: find a biological entity (usually a protein) whose
  modulation is hypothesized to change a disease phenotype. Evidence sources: literature, pathway
  biology, human genetics, patient samples. "Validation" means building enough in vitro/in vivo/
  human evidence that manipulating the target plausibly affects the disease — not just correlating
  with it.
- **Hit generation**: high-throughput screening (HTS) of large compound/molecule libraries against
  the target (or a phenotypic assay), or structure-based/virtual screening, to find "hits" — things
  that show the desired activity at all. **Pan-assay interference compounds (PAINS)** are a known
  trap here — compounds that look active in many unrelated assays for artifactual reasons and get
  filtered out.
- **Hit-to-lead / Lead optimization**: iteratively improve affinity, selectivity, potency,
  developability (a very drug-discovery-specific word — see §3), PK/PD, and formulation, using
  structure-activity relationships (SAR). This is where most attrition happens: each round trades
  off multiple properties simultaneously (potent enough, but also selective enough, also
  synthesizable, also not immunogenic, also stable enough...).
- **Candidate selection (CS)**: pick the single molecule that moves into formal development.
- **Preclinical**: toxicology (Tox), ADME (Absorption, Distribution, Metabolism, Excretion),
  PK/PD (pharmacokinetics/pharmacodynamics) studies — required before dosing humans.
- **Clinical phases**: Phase I (safety, first human dose), Phase II (efficacy signal), Phase III
  (large confirmatory trials), then regulatory submission/registration and launch.

**Cost/scale context**: historically cited industry figures put the fully-loaded cost per approved
new molecular entity around $1–2B, with a large majority of candidates failing somewhere in this
pipeline (attrition is the central economic fact of the industry — most of what's screened, and
even most of what reaches clinical trials, never becomes a drug). Only a small fraction (~667 of
~20,000 human proteins, per Lilly's own NTM slide, citing Dammes et al. 2020) have ever been
successfully drugged — the rest are informally called "undruggable" targets, a major current R&D
frontier.

**Two discovery philosophies** worth knowing the names of:
- **Reverse pharmacology**: start from a disease/target hypothesis, then find molecules that hit
  it (the dominant modern paradigm, enabled by genome sequencing).
- **Forward/phenotypic pharmacology**: screen for a desired phenotypic effect first, then work
  backward to figure out which target is responsible ("target deconvolution").

---

## 2. What a biological target actually is

A **biological target** is anything in a living organism that a drug (or an endogenous ligand) is
directed at or binds to, causing a change in its behavior/function. In practice, in pharma, this
means overwhelmingly **proteins**:

- **GPCRs (G protein-coupled receptors)** — the single largest class, ~50% of marketed drug
  targets.
- **Enzymes** — kinases, proteases, esterases, phosphatases.
- **Ion channels** — ligand-gated and voltage-gated.
- **Nuclear hormone receptors.**
- **Structural / membrane transport proteins.**
- **Nucleic acids (DNA/RNA)** — a newer and growing target class (relevant to siRNA/ASO/gene-editor
  modalities, see §9).

**Binding mechanisms**: noncovalent (weak, reversible — most common), reversible covalent, or
irreversible covalent. **Functional outcomes**: antagonism (block), agonism (activate), or direct
enzyme modulation.

**Druggability** is the specific, load-bearing term for "can this target realistically be hit with
a molecule at all" — distinct from "is this target biologically important." A biologically
critical, disease-validated target can still be practically undruggable (no good binding pocket,
wrong subcellular location, etc.), which is exactly the gap Lilly's NTM group exists to close (see
§9).

**Ecotoxicology note** (minor but real): targets are evolutionarily conserved across species, so
pharmaceuticals that reach waterways can act on the same target in wildlife (e.g., fish
feminization from hormone-active compounds in wastewater) — a reminder that "target" is a
biological concept, not a human-specific one.

---

## 3. Genes and proteins — the minimum vocabulary

- **DNA**: the molecule encoding genetic information as sequences of base pairs.
- **Gene**: the basic physical/functional unit of heredity — a DNA sequence (hundreds to millions
  of base pairs); humans have ~19,900 genes, two copies of each (one per parent).
- **Chromosome**: the structure that organizes many genes together, linearly.
- **Allele**: a variant form of the same gene (small sequence differences) — the molecular basis of
  individual variation.
- **Gene → protein**: many (not all) genes encode instructions to build proteins, which do the
  actual biological work; other genes are regulatory rather than protein-coding. (The classic
  "central dogma" — DNA → RNA transcription → protein translation — is the mechanism, though the
  MedlinePlus source used here doesn't spell out transcription/translation explicitly; worth a
  deeper look if a challenge task touches gene expression directly.)
- **Mutation / expression**: not covered in the primer source used here — flag as a gap to fill in
  if the actual challenge turns out to hinge on genetic-variant or expression-level data.

Practically: most "targets" in drug discovery data are **proteins encoded by specific genes**,
which is why target databases (UniProt) are organized around protein/gene identifiers, not free-text
names — the same target can have many synonyms in the literature, but should resolve to one
canonical identifier. This is exactly the kind of entity-resolution problem MDM (§7) is built to
solve.

---

## 4. UniProt — the protein/target reference

- **What it is**: "the Universal Protein resource" — a merged, curated database (from Swiss-Prot,
  TrEMBL, and PIR-PSD), maintained by EBI, SIB, and PIR.
- **Two-tier structure inside UniProtKB**:
  - **Swiss-Prot**: manually curated, non-redundant, expert-annotated (~569K entries as of Feb
    2023) — the "gold standard" tier.
  - **TrEMBL**: computationally annotated, much larger (~246M entries) — high volume, lower
    per-entry curation confidence, generated to keep up with genome-sequencing throughput.
- **What's in an entry**: sequence, function, enzyme classification, subcellular location,
  protein-protein interactions, post-translational modifications, domains, and literature- or
  prediction-derived variant information.
- **Identifiers**: stable accession numbers (Swiss-Prot) and UPI codes (UniParc, the
  all-sequences archive) — the actual "master ID" you'd match other datasets against.
- **Formats**: FASTA, XML, RDF, flat file — i.e., built to be machine-consumed, not just browsed.

**Why this matters for a challenge**: if a task involves "targets," UniProt accession numbers are
almost certainly the canonical join key underneath whatever human-readable target names appear in
the data — and Swiss-Prot vs. TrEMBL provenance is itself a data-quality/confidence signal worth
carrying through any pipeline (a TrEMBL-only, uncurated protein record is a weaker
data-quality footing than a Swiss-Prot one).

---

## 5. ChEMBL — the bioactivity reference

- **What it is**: a manually curated database of **bioactive, drug-like molecules**, combining
  chemical structures, bioactivity measurements, and genomic information — purpose-built to help
  translate genomic/target findings into actual drug candidates.
- **Core entities** (from its schema): compounds, targets, assays, and the bioactivity
  measurements that link them (a compound tested against a target in a specific assay produces one
  or more activity values).
- **Ecosystem tools**: **UniChem** (cross-references chemical identifiers across databases —
  itself an MDM-flavored tool) and **SureChEMBL** (patent-derived compounds).
- **License/status**: CC BY-SA 3.0; an ELIXIR Core Data Resource / Global Core Biodata Resource —
  i.e., a resource explicitly recognized as critical, long-term infrastructure, not a side project.

**Why this matters**: ChEMBL is the likely shape of any "compound × target × activity" dataset in
a challenge — expect columns resembling compound ID, target ID (often a UniProt accession or
ChEMBL target ID), assay description, and a measured activity value with a unit and a type (see
§6 for what those values actually mean).

---

## 6. BindingDB — the binding-affinity reference

- **What it is**: billed as "the first public molecular recognition database" — ~3.2M binding
  measurements across ~1.4M compounds and ~11,500 protein targets (1.6M of those measurements
  BindingDB-curated).
- **What it measures**: experimentally measured binding affinities — **Ki, Kd, IC50, EC50**, rate
  constants, and thermodynamic parameters (ΔG°, ΔH°, -TΔS°) — sourced from enzyme inhibition
  assays, ITC, NMR, and other biophysical methods.
- **Relationship to ChEMBL**: BindingDB actually **imports ChEMBL records** (for well-defined
  protein targets) alongside literature/patent/PubChem-sourced entries, and re-curates on top —
  so there's real overlap, and real potential for **conflicting values for the same
  compound-target pair** reported by different sources/methods. This is a concrete, well-known
  data-quality fault line in the domain (same nominal measurement, different assay conditions,
  different reported numbers) — a strong candidate for what a "clean this dataset" task would
  actually be testing.
- **Licensing nuance**: ChEMBL-derived rows are CC BY-SA 3.0; BindingDB's own curated rows are CC
  BY 3.0 — i.e., even *license/provenance* is a per-row attribute, not a whole-dataset one.

**The key terms to know cold, since they're not interchangeable**:
- **Ki** — inhibition constant (binding affinity in a competitive-inhibition model).
- **Kd** — dissociation constant (direct binding affinity).
- **IC50** — concentration causing 50% inhibition of a measured effect (assay- and
  condition-dependent, not a pure biophysical constant).
- **EC50** — concentration causing 50% of maximal effect (for agonists/functional response).
- Lower Ki/Kd/IC50/EC50 = more potent. These four are commonly confused/mixed in casual
  data but are **not the same physical quantity** — a real data-quality check on this kind of
  dataset would specifically flag rows where value *type* isn't tracked alongside value
  *magnitude*, since a "IC50 = 10nM" and "Kd = 10nM" are not directly comparable numbers.

---

## 7. Master Data Management (MDM) — the enterprise lens

- **What it is**: the discipline of ensuring "uniformity, accuracy, stewardship, semantic
  consistency, and accountability" for an organization's core shared data entities.
- **Core goals**: consistency/accuracy (no duplicates/conflicts), a single version of the truth
  (SVOT) for decision-making, operational efficiency, regulatory compliance.
- **Core concepts**:
  - **Golden record** — the one authoritative, de-duplicated version of an entity (e.g., "the"
    record for a given protein target, reconciled across UniProt/ChEMBL/BindingDB-style sources).
  - **Entity resolution** — matching/linking records that refer to the same real-world thing across
    systems that don't share a key (e.g., the same target under different synonyms/IDs).
  - **Governance/stewardship** — Data Owners set the rules, Data Stewards execute them day to day.
  - **Implementation patterns**: source-of-record, registry, consolidation, coexistence,
    centralized — different strategies for *where* the golden record actually lives relative to
    the source systems.
- **Common failure modes**: redundancy from siloed business units, painful reconciliation during
  mergers/database consolidations, stakeholders disagreeing on what "the same entity" even means,
  and general resource intensity of doing this well.

**Direct mapping to §4–6**: UniProt, ChEMBL, and BindingDB are exactly the kind of
independently-governed, overlapping reference sources MDM exists to reconcile — same target, same
compound, same interaction, described with different IDs, different curation depth, and
occasionally different reported values. If the challenge is MDM-flavored, expect tasks like:
building a target/compound crosswalk, picking a golden value when sources disagree, or scoring
records by provenance/curation-tier confidence (Swiss-Prot > TrEMBL; BindingDB-curated >
literature-imported, etc.).

---

## 8. Data Quality — the practical checklist

**Dimensions** commonly assessed: accuracy/correctness, completeness, consistency, timeliness,
validity, uniqueness, comparability, accessibility, credibility.

**Common problems**: invalid/outdated values, data-entry and migration errors, inconsistency
across systems, failure of updates to propagate everywhere a value is duplicated.

**Standard remediation toolkit**:
1. **Profiling** — understand what's actually in the dataset before touching it (distribution,
   nulls, cardinality, outliers) — directly analogous to the audit-first discipline from the
   RetailCast challenge (see [[forecasting-challenge-playbook]] §1).
2. **Standardization** — enforce consistent formats/units (critical here: Ki/Kd/IC50/EC50 unit and
   type normalization, per §6).
3. **Geocoding** — address-specific, likely N/A here, but the general pattern ("normalize against
   an authoritative reference") maps directly to resolving target/compound IDs against
   UniProt/ChEMBL canonical identifiers.
4. **Matching/linking (fuzzy)** — the entity-resolution step from MDM (§7), applied to target
   synonyms, compound name variants, etc.
5. **Monitoring** — track quality metrics over time, not just once.
6. **Continuous/embedded cleansing** — build quality checks into the pipeline rather than doing a
   one-off cleanup.

**Carry-over from the RetailCast playbook**: the same evidence-first instinct applies here —
"finding a data problem and saying so, with concrete numbers, scores more than silently getting a
good-looking result" generalized from forecasting to any data challenge. If this challenge is
data-quality/MDM-flavored, the graded artifact is very plausibly going to reward *naming specific,
evidenced defects* (e.g., "target X has 3 conflicting Kd values across sources, ranging Y–Z,
because assay condition wasn't normalized") over a silently-produced "clean" output nobody can
audit.

---

## 9. Lilly's own discovery pipeline & organizational vocabulary (from internal decks)

These two documents are Lilly-internal process/org context, not applicable data science tooling —
useful mainly to speak the domain's language and to recognize milestone names if a challenge
dataset uses them.

**Milestone sequence** (Discovery phase, consistent across both documents):
`Target → Hit → Lead → Portfolio Entry (PE) → Candidate Identification (CI) → Candidate Selection
(CS) → First Human Dose (FHD) / First Toxicology Dose (FTD) → Phase I/II/III → Launch`

- **Target**: sufficient evidence that modulating it affects the disease phenotype, and it fits the
  therapeutic area's strategy.
- **Hit**: molecules with the desired target-modulation property have been identified; asset
  profile/differentiation strategy defined enough to start optimizing.
- **Portfolio Entry (PE)**: project formally enters the funded portfolio with approved scope/budget
  through FHD — usually aligned with Hit for small/large-molecule projects, or with Lead for
  genetic-medicine projects.
- **Lead**: one or more molecules/chemical scaffolds identified with real potential to become the
  Candidate Selection molecule.
- **Candidate Selection (CS)**: the molecule chosen to move into formal clinical development.
- Typical **archetype timeline**: ~36 months from PE to FHD (varies significantly by modality).

**Modalities mentioned** (i.e., what kind of molecule is being developed against a target) —
useful vocabulary since a target/compound dataset would need to know which applies:
Small Molecule (SM), Large Molecule/antibody (LM), Peptide, ADC (antibody-drug conjugate), siRNA,
ASO (antisense oligonucleotide), AAV (gene therapy vector), gene editors. Portfolio composition
has been shifting toward these newer modalities (siRNA, ADCs, ASO, AAV, gene editors) — each adds
its own new data types/assays and its own druggability logic (nucleic-acid targets, delivery
route, immunogenicity risk, etc.).

**Key functional groups** (org chart flavor, only worth knowing as acronym decoder, not deeply):
BioTDR (Biotechnology Discovery Research), DCRT (Discovery Chemistry Research & Technologies), NTM
(New Therapeutic Modalities — explicitly chartered to go after "undruggable" targets), ATPLV
(ADME/Tox/PK-PD/LEM/Veterinary), CMC (Chemistry Manufacturing Control), SMDD (Synthetic Molecule
Design & Development).

**Full acronym list** (from the BRIDGE deck, kept verbatim for reference):

| Acronym | Meaning |
|---|---|
| TA | Therapeutic Area |
| BioTDR | Biotechnology Discovery Research |
| SAR | Structure-Activity Relationship |
| NPR | New Product Resupply (protein expression & purification group) |
| PET | Protein Expression Team |
| ATPLV | ADME, Toxicology, PK/PD, LEM, Veterinary Resources |
| ADME | Absorption, Distribution, Metabolism, Excretion |
| LEM | Laboratory of Experimental Medicine |
| DCRT | Discovery Chemistry Research & Technology |
| CMC | Chemistry Manufacturing Control |
| FHD | First Human Dose |
| SAD / MAD | Single/Multiple Ascending Dose |
| DDCS | Delivery, Device and Connected Solutions |
| API | Active Pharmaceutical Ingredient (also a department name) |
| PD | Product Delivery |
| BR&D | Bioproduct Research and Development |
| NTM | New Therapeutic Modalities |
| SMDD | Synthetic Molecule Design and Development |
| DRQS | Discovery Research Quality Systems |
| LQS | Lilly Quality System |
| PR&D | Product Research & Development |

**Undruggable-target framing (NTM slide, notable specific stat)**: of ~20,000 human proteins, only
~667 had been successfully targeted by approved drugs as of 2017 (Dammes et al., Trends Pharmacol
Sci 2020) — i.e., roughly 3% "hit rate" at the whole-proteome level, framed explicitly as the
opportunity NTM's platforms (nucleic-acid modalities, novel engineering) exist to close.

---

## 10. Lilly's Discovery *Project Management* vocabulary (from the onboarding deck)

This deck is about **portfolio/process management**, not science — lower priority for a data
challenge, but captured in case a challenge references portfolio/milestone data specifically
(the deck emphasizes that milestone-date *accuracy* is itself treated as a company-wide,
governance-relevant data quality problem — a nice real-world echo of §8):

- **Two Discovery sub-phases**: Pre-Portfolio (Pre-Target → PE) and PE → Candidate Identification
  (CI) — timelines differ heavily by modality/technical difficulty.
- **Milestone confidence levels**: High (>80%), Medium (50–80%), Low (25–50%), Very Low (<25%),
  Pending Change, Archetype (not yet planned, >18–24 months out) — i.e., Lilly formally tracks a
  *confidence* attribute alongside every forecasted milestone date, which is directly analogous to
  attaching a trust/uncertainty band to a forecast (echoes the RetailCast `trust_report.csv`
  pattern in [[forecasting-challenge-playbook]]).
  quote (verbatim, notable): *"Major milestone data is used at all levels of the company... the
  accuracy of milestones is directly impactful to the portfolio."*
- **Administrative milestone states**: Initiate, Terminate, Parked (<6 months, unfunded,
  reactivatable), Reactivate, Alliance Start/Stop — a small, well-defined state machine, worth
  knowing if a challenge involves portfolio/pipeline-status data.
- **Explicit acknowledged pain point** (deck's own "Key Takeaways," verbatim theme): *"Archetypes
  and models cannot keep pace with the changes. The lack of accurate models leads to more
  unpredictability... and lots of time-consuming manual manipulation for early program
  projections."* — i.e., Lilly itself names *forecasting/planning-model staleness for new
  modalities* as an open, acknowledged problem. Worth remembering as a plausible challenge angle
  in its own right (a forecasting problem *about* Discovery timelines/costs, not just about
  target/compound data) — distinct from, but not incompatible with, the MDM/data-quality
  hypothesis in §0.

---

## 11. Prep checklist for whenever the real problem statement lands

- [ ] Confirm which hypothesis from §0 is right (MDM/data-quality on reference data, vs. a
      forecasting problem on Discovery timelines/costs, vs. something else) — re-read the eval
      contract first, per [[forecasting-challenge-playbook]] §1, before assuming either.
- [ ] If it's reference-data-shaped: expect compound/target/assay entities and Ki/Kd/IC50/EC50-style
      activity values; budget time for unit/type normalization and source-provenance tracking (§6–8)
      before any modeling.
- [ ] If it's portfolio/timeline-shaped: expect milestone-date and confidence-level fields; the
      RMSSE/backtest discipline from the RetailCast playbook likely still applies directly.
- [ ] Either way: apply the audit-first, evidence-with-numbers, baseline-before-clever discipline
      from [[forecasting-challenge-playbook]] — it's domain-agnostic and was explicitly validated
      as the right approach on the prior challenge.
- [ ] Revisit UniProt/ChEMBL/BindingDB's actual public schemas (not just this summary) once real
      data is in hand — this primer is directional, not a substitute for reading the real data
      dictionary.
