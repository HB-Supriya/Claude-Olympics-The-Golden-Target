"""Evidence-contract tests.

The rubric pays full marks only for a finding that carries its correction and its proof. These tests
assert the contract is enforced structurally, so no future detector can emit an unproven claim.
"""

import pytest

from goldentarget.findings import EvidenceError, Finding, merge_findings


def make(**overrides):
    kwargs = dict(
        gene="PIM1",
        observed="Q9P1W9",
        correct="P11309",
        retrieved_evidence='{"accession": "P11309", "gene": {"name": "PIM1"}}',
        evidence_source="EBI Proteins API GET /proteins?accession=P11309",
        classification="wrong_accession_mapping",
    )
    kwargs.update(overrides)
    return Finding(**kwargs)


class TestEvidenceContract(object):
    @pytest.mark.parametrize("field", ["observed", "correct", "retrieved_evidence", "evidence_source"])
    def test_missing_evidence_field_is_refused(self, field):
        with pytest.raises(EvidenceError) as excinfo:
            make(**{field: ""})
        assert field in str(excinfo.value)

    @pytest.mark.parametrize("field", ["observed", "correct", "retrieved_evidence", "evidence_source"])
    def test_whitespace_only_is_refused(self, field):
        with pytest.raises(EvidenceError):
            make(**{field: "   "})

    def test_complete_finding_is_accepted(self):
        finding = make()
        assert finding.severity == "high"
        assert finding.to_dict()["correct"] == "P11309"

    def test_severity_reflects_classification(self):
        assert make(classification="stale_gene_symbol").severity == "low"
        assert make(classification="obsolete_accession").severity == "medium"
        assert make(classification="organism_mismatch").severity == "high"


class TestMerge(object):
    def test_same_defect_in_two_rows_reports_once_with_both_locations(self):
        a = make(locations=["source_chembl.csv row 2 (CHEMBL2147)"])
        b = make(locations=["source_bindingdb.csv row 9 (Q9P1W9)"])
        merged = merge_findings([a, b])
        assert len(merged) == 1
        assert len(merged[0].locations) == 2

    def test_distinct_defective_values_are_kept_apart(self):
        a = make(observed="Q9P1W9", locations=["r1"])
        b = make(observed="Q969F8", correct="Q15726", gene="KISS1", locations=["r2"])
        assert len(merge_findings([a, b])) == 2

    def test_most_consequential_label_wins_for_one_value(self):
        high = make(classification="wrong_accession_mapping", locations=["r1"])
        low = make(classification="stale_gene_symbol", locations=["r1"])
        merged = merge_findings([low, high])
        assert len(merged) == 1
        assert merged[0].classification == "wrong_accession_mapping"

    def test_output_is_sorted_most_severe_first(self):
        findings = merge_findings([
            make(classification="stale_gene_symbol", observed="A", locations=["r1"]),
            make(classification="wrong_accession_mapping", observed="B", locations=["r2"]),
            make(classification="obsolete_accession", observed="C", locations=["r3"]),
        ])
        assert [f.severity for f in findings] == ["high", "medium", "low"]
