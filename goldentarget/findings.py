"""The finding type and its evidence contract.

The rubric is explicit: a finding earns full credit only when it carries both the observed and the
corrected value, and a quarter-credit "this looks wrong" is worse than useless if it also costs
precision. So the contract is enforced *structurally* — ``Finding`` raises if any of the four
evidence fields is missing. A detector cannot emit an unproven claim even by accident; the only way
to stay silent is to not emit at all, which is exactly the behaviour we want when the authority
could not be reached.
"""

# Severity reflects blast radius on the target master, per the brief's instruction to treat a wrong
# mapping, a stale-but-valid label and a duplicate identity as different problems.
#
#   high   — the record points at the wrong protein. Assays, literature and programme decisions
#            attach to the wrong entity; silently corrupts the master.
#   medium — the identity is right but the key is dead, duplicated, or cross-referenced wrongly.
#            Fragments one real target into several records, or breaks joins to other systems.
#   low    — the label is stale or absent but still denotes the right entity. Cosmetic to a human,
#            but it defeats exact-match joins and search.
SEVERITY = {
    "wrong_accession_mapping": "high",
    "wrong_gene_symbol": "high",
    "organism_mismatch": "high",
    "invalid_accession": "high",
    "isoform_accession": "medium",
    "wrong_crossreference": "medium",
    "obsolete_accession": "medium",
    "duplicate_identity": "medium",
    "duplicate_registration": "medium",
    "ambiguous_mention": "medium",
    "secondary_accession": "low",
    "stale_gene_symbol": "low",
    "unknown_gene_symbol": "low",
    "missing_gene_symbol": "low",
}

# When one row is defective in several ways, report it once under its most consequential label.
PRECEDENCE = (
    "wrong_accession_mapping",
    "invalid_accession",
    "wrong_gene_symbol",
    "isoform_accession",
    "organism_mismatch",
    "duplicate_identity",
    "obsolete_accession",
    "wrong_crossreference",
    "secondary_accession",
    "duplicate_registration",
    "ambiguous_mention",
    "stale_gene_symbol",
    "unknown_gene_symbol",
    "missing_gene_symbol",
)
_PRECEDENCE_INDEX = {name: index for index, name in enumerate(PRECEDENCE)}

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class EvidenceError(ValueError):
    """Raised when a caller tries to build a finding without complete evidence."""


class Finding(object):
    """One defect, with the proof attached.

    ``observed`` is the defective value verbatim from the file; ``correct`` is the authority's
    value; ``retrieved_evidence`` is what the authority literally returned; ``evidence_source``
    names the endpoint that returned it.
    """

    __slots__ = (
        "gene", "observed", "correct", "retrieved_evidence", "evidence_source",
        "classification", "severity", "field", "impact", "reasoning", "locations", "source_files",
    )

    def __init__(self, gene, observed, correct, retrieved_evidence, evidence_source,
                 classification, field="", impact="", reasoning="", locations=None,
                 source_files=None):
        missing = [
            name for name, value in (
                ("observed", observed),
                ("correct", correct),
                ("retrieved_evidence", retrieved_evidence),
                ("evidence_source", evidence_source),
            ) if not str(value or "").strip()
        ]
        if missing:
            raise EvidenceError(
                "refusing to emit a %s finding without %s" % (classification, ", ".join(missing))
            )
        self.gene = str(gene or "").strip()
        self.observed = str(observed).strip()
        self.correct = str(correct).strip()
        self.retrieved_evidence = str(retrieved_evidence).strip()
        self.evidence_source = str(evidence_source).strip()
        self.classification = classification
        self.severity = SEVERITY.get(classification, "medium")
        self.field = field
        self.impact = impact
        self.reasoning = reasoning
        self.locations = list(locations or ())
        self.source_files = sorted(set(source_files or ()))

    def key(self):
        """Identity for de-duplication: the same wrong value in five rows is one defect."""
        return (self.classification, self.gene.upper(), self.observed, self.correct)

    def sort_key(self):
        return (
            _SEVERITY_ORDER.get(self.severity, 3),
            _PRECEDENCE_INDEX.get(self.classification, 99),
            self.gene.upper(),
            self.observed,
        )

    def to_dict(self):
        payload = {
            "gene": self.gene,
            "observed": self.observed,
            "correct": self.correct,
            "retrieved_evidence": self.retrieved_evidence,
            "evidence_source": self.evidence_source,
            "severity": self.severity,
            "classification": self.classification,
        }
        if self.field:
            payload["field"] = self.field
        if self.source_files:
            payload["source_files"] = self.source_files
        if self.locations:
            payload["locations"] = self.locations
        if self.reasoning:
            payload["reasoning"] = self.reasoning
        if self.impact:
            payload["impact"] = self.impact
        return payload


def merge_findings(findings):
    """Collapse duplicates and keep one label per (row, defective value).

    Two passes:
      1. identical (classification, gene, observed, correct) findings merge, pooling their
         locations — one defect reported once, with every place it occurs.
      2. where the same file value is implicated by several classifications, keep only the most
         consequential one, so the report reads as a diagnosis rather than a pile of symptoms.
    """
    merged = {}
    for finding in findings:
        key = finding.key()
        existing = merged.get(key)
        if existing is None:
            merged[key] = finding
            continue
        existing.locations = sorted(set(existing.locations) | set(finding.locations))
        existing.source_files = sorted(set(existing.source_files) | set(finding.source_files))

    best_per_value = {}
    for finding in merged.values():
        value_key = (finding.gene.upper(), finding.observed, tuple(finding.locations))
        incumbent = best_per_value.get(value_key)
        if incumbent is None or finding.sort_key() < incumbent.sort_key():
            best_per_value[value_key] = finding

    return sorted(best_per_value.values(), key=lambda f: f.sort_key())
