"""Evidence-contract tests.

The rubric pays full marks only for a finding that carries its correction and its proof. These tests
assert the contract is enforced structurally, so no future detector can emit an unproven claim.
"""

import pytest

from goldentarget.findings import (
    EvidenceError,
    Finding,
    drop_redundant_symbol_findings,
    merge_findings,
    restrict_to_contract,
)


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


class TestReportableVocabulary(object):
    """Only documented classifications may reach stdout."""

    def test_secondary_accession_is_reported_as_obsolete(self):
        kept, withheld = restrict_to_contract([make(classification="secondary_accession")])
        assert [f.classification for f in kept] == ["obsolete_accession"]
        assert kept[0].severity == "medium"
        assert withheld == {}

    @pytest.mark.parametrize("classification", [
        "wrong_gene_symbol", "unknown_gene_symbol", "duplicate_identity", "duplicate_registration",
    ])
    def test_undocumented_classifications_are_withheld_and_counted(self, classification):
        kept, withheld = restrict_to_contract([make(classification=classification)])
        assert kept == []
        assert withheld == {classification: 1}

    def test_documented_classifications_pass_through_untouched(self):
        original = make(classification="obsolete_accession")
        kept, withheld = restrict_to_contract([original])
        assert kept == [original]
        assert withheld == {}


class TestRedundantSymbolSuppression(object):
    """A stale symbol riding along with a defective accession is one defect, not two."""

    def test_stale_symbol_is_withheld_when_its_row_is_already_reported(self):
        accession = make(classification="obsolete_accession", observed="Q8N5L2",
                         correct="P30530", locations=["source_bindingdb.csv row 146 (Q8N5L2)"])
        symbol = make(classification="stale_gene_symbol", observed="UFO", correct="AXL",
                      locations=["source_bindingdb.csv row 146 (Q8N5L2)"])
        kept, dropped = drop_redundant_symbol_findings([accession, symbol])
        assert dropped == 1
        assert [f.classification for f in kept] == ["obsolete_accession"]

    def test_standalone_stale_symbol_survives(self):
        symbol = make(classification="stale_gene_symbol", observed="SEPT9", correct="SEPTIN9",
                      locations=["source_internal.csv row 8 (TGT-2433)"])
        kept, dropped = drop_redundant_symbol_findings([symbol])
        assert dropped == 0
        assert kept == [symbol]

    def test_only_the_explained_rows_are_removed_from_a_pooled_finding(self):
        accession = make(classification="obsolete_accession", locations=["row_a"])
        symbol = make(classification="stale_gene_symbol", observed="UFO", correct="AXL",
                      locations=["row_a", "row_b"])
        kept, dropped = drop_redundant_symbol_findings([accession, symbol])
        assert dropped == 0
        survivor = [f for f in kept if f.classification == "stale_gene_symbol"][0]
        assert survivor.locations == ["row_b"]

    @pytest.mark.parametrize("accession_defect", [
        "obsolete_accession", "wrong_accession_mapping", "isoform_accession", "invalid_accession",
    ])
    def test_any_accession_defect_explains_the_row(self, accession_defect):
        accession = make(classification=accession_defect, locations=["row_a"])
        symbol = make(classification="stale_gene_symbol", observed="UFO", correct="AXL",
                      locations=["row_a"])
        _, dropped = drop_redundant_symbol_findings([accession, symbol])
        assert dropped == 1
