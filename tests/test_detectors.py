"""Detector tests, replayed offline against recorded authority responses.

Each test states the defect the detector exists to catch and the correction it must produce, plus —
just as importantly — the near-miss cases it must stay silent about.
"""

from goldentarget import detectors, golden
from .stubs import resolved_offline


def resolved_pack():
    """Load the mini pack and resolve it offline, once per test that needs it."""
    return resolved_offline()


def by_observed(findings):
    return {f.observed: f for f in findings}


class TestAccessionLifecycle(object):
    def test_merged_accession_is_corrected_to_its_successor(self):
        authority, _, rows = resolved_pack()
        found = by_observed(detectors.detect_accession_status(authority, rows))
        assert found["B5A968"].correct == "P29317"
        assert found["B5A968"].classification == "obsolete_accession"
        assert "MERGED" in found["B5A968"].retrieved_evidence

    def test_multi_hop_merge_chain_resolves_to_the_live_entry(self):
        # E9PGB9 -> Q86YH7 -> P56524. Stopping at the first hop would hand back another dead key.
        authority, _, rows = resolved_pack()
        found = by_observed(detectors.detect_accession_status(authority, rows))
        assert found["E9PGB9"].correct == "P56524"
        assert "Q86YH7" in found["E9PGB9"].reasoning

    def test_live_accessions_are_left_alone(self):
        authority, _, rows = resolved_pack()
        observed = by_observed(detectors.detect_accession_status(authority, rows))
        for accession in ("P11309", "Q9P1W9", "P29317", "P07288", "P55786"):
            assert accession not in observed

    def test_every_finding_carries_full_evidence(self):
        authority, _, rows = resolved_pack()
        for finding in detectors.detect_accession_status(authority, rows):
            assert finding.observed and finding.correct
            assert finding.retrieved_evidence and finding.evidence_source


class TestInvalidAccession(object):
    def test_malformed_accession_is_repaired_from_the_gene_symbol(self):
        authority, _, rows = resolved_pack()
        found = by_observed(detectors.detect_invalid_accession(authority, rows))
        assert found["P0521X"].correct == "P00519"  # ABL1
        assert found["P0521X"].classification == "invalid_accession"

    def test_valid_accessions_are_not_flagged(self):
        authority, _, rows = resolved_pack()
        observed = by_observed(detectors.detect_invalid_accession(authority, rows))
        assert "P11309" not in observed
        assert "B5A968" not in observed  # obsolete, but well-formed and known


class TestIsoformAccession(object):
    def test_isoform_identifier_is_corrected_to_its_parent_entry(self):
        authority, _, rows = resolved_pack()
        found = by_observed(detectors.detect_isoform_accession(authority, rows))
        assert found["Q13422-3"].correct == "Q13422"
        assert found["Q13422-3"].classification == "isoform_accession"

    def test_evidence_quotes_the_parents_isoform_list(self):
        authority, _, rows = resolved_pack()
        found = by_observed(detectors.detect_isoform_accession(authority, rows))
        assert "ALTERNATIVE_PRODUCTS" in found["Q13422-3"].retrieved_evidence
        assert "Q13422-1" in found["Q13422-3"].retrieved_evidence

    def test_plain_accessions_are_not_flagged(self):
        authority, _, rows = resolved_pack()
        assert not [
            f for f in detectors.detect_isoform_accession(authority, rows)
            if "-" not in f.observed
        ]


class TestOrganism(object):
    def test_cross_species_accession_is_flagged(self):
        authority, _, rows = resolved_pack()
        findings = detectors.detect_organism(authority, rows)
        assert any(f.observed == "Homo sapiens" and "Mus musculus" in f.correct for f in findings)

    def test_tax_id_disagreement_is_reported_as_its_own_value(self):
        authority, _, rows = resolved_pack()
        findings = detectors.detect_organism(authority, rows)
        assert any(f.field == "tax_id" and f.observed == "9606" and f.correct == "10090"
                   for f in findings)

    def test_spelling_variants_are_never_flagged(self):
        # The mini pack spells human four ways; none of them is a defect.
        authority, _, rows = resolved_pack()
        findings = detectors.detect_organism(authority, rows)
        for finding in findings:
            assert "Mus" in finding.correct or finding.correct == "10090"


class TestSymbol(object):
    def test_synonym_is_a_stale_label_not_a_wrong_mapping(self):
        authority, _, rows = resolved_pack()
        found = by_observed(detectors.detect_symbol(authority, rows))
        assert found["CSVP"].classification == "stale_gene_symbol"
        assert found["CSVP"].correct == "ADAM17"
        assert found["CSVP"].severity == "low"

    def test_renamed_symbol_is_corrected(self):
        authority, _, rows = resolved_pack()
        found = by_observed(detectors.detect_symbol(authority, rows))
        assert found["WHSC1"].correct == "NSD2"

    def test_wrong_accession_beats_wrong_symbol_when_name_backs_the_symbol(self):
        # ChEMBL row: gene PIM1 + name "...pim-1", but accession Q9P1W9 (PIM2). Two of the row's
        # three identity fields agree, so the accession is the defective one.
        authority, _, rows = resolved_pack()
        found = by_observed(detectors.detect_symbol(authority, rows))
        assert found["Q9P1W9"].classification == "wrong_accession_mapping"
        assert found["Q9P1W9"].correct == "P11309"

    def test_bare_symbol_as_target_name_still_backs_the_symbol(self):
        # BindingDB row: gene KISS1, name "KISS1", accession Q969F8 (KISS1R).
        authority, _, rows = resolved_pack()
        found = by_observed(detectors.detect_symbol(authority, rows))
        assert found["Q969F8"].correct == "Q15726"

    def test_missing_symbol_is_filled_from_the_authority(self):
        authority, _, rows = resolved_pack()
        found = by_observed(detectors.detect_symbol(authority, rows))
        assert found["(empty gene_symbol)"].correct == "IL1B"

    def test_correct_symbols_are_silent(self):
        authority, _, rows = resolved_pack()
        observed = by_observed(detectors.detect_symbol(authority, rows))
        for symbol in ("PIM1", "PIM2", "EPHA2", "KLK3", "NPEPPS", "PDE7A", "PDE10A"):
            assert symbol not in observed


class TestCrossReferences(object):
    def test_chembl_id_belonging_to_another_entry_is_corrected(self):
        authority, _, rows = resolved_pack()
        found = by_observed(detectors.detect_crossreferences(authority, rows))
        assert found["CHEMBL3012"].correct == "CHEMBL4409"
        assert found["CHEMBL3012"].classification == "wrong_crossreference"

    def test_correct_chembl_ids_are_silent(self):
        authority, _, rows = resolved_pack()
        observed = by_observed(detectors.detect_crossreferences(authority, rows))
        for identifier in ("CHEMBL2147", "CHEMBL4523", "CHEMBL2068", "CHEMBL2099"):
            assert identifier not in observed


class TestAmbiguousMentions(object):
    def _mentions(self):
        authority, pack, rows = resolved_pack()
        clusters = golden.build_clusters(authority, rows, {})
        return detectors.detect_ambiguous_mentions(
            authority, pack["publications"], clusters, default_tax_id="9606"
        )

    def _rows_by_gene(self):
        """One finding is emitted per publication row here; the pipeline merges them later."""
        grouped = {}
        for finding in self._mentions():
            grouped.setdefault(finding.correct, []).extend(finding.locations)
        return grouped

    def test_shared_alias_resolves_from_the_context_sentence(self):
        findings = self._mentions()
        assert {f.correct for f in findings} == {"KLK3", "NPEPPS"}
        for finding in findings:
            assert finding.observed == "PSA"

    def test_kallikrein_sentence_goes_to_klk3_and_puromycin_to_npepps(self):
        grouped = self._rows_by_gene()
        klk3_rows = " ".join(grouped["KLK3"])
        npepps_rows = " ".join(grouped["NPEPPS"])
        assert "30099162" in klk3_rows   # semenogelins / seminal coagulum
        assert "30010616" in klk3_rows   # serum glycoprotein / biopsy
        assert "30087819" in npepps_rows  # puromycin sensitivity
        assert "30087819" not in klk3_rows

    def test_unambiguous_mentions_are_not_flagged(self):
        findings = self._mentions()
        assert all(f.observed == "PSA" for f in findings)

    def test_pmid_metadata_is_never_used_as_evidence(self):
        # pmids are internal reference numbers; some collide with unrelated real papers. Nothing in
        # a finding may derive from the pmid, journal or year columns.
        for finding in self._mentions():
            blob = (finding.retrieved_evidence + finding.evidence_source + finding.reasoning).lower()
            assert "pubmed" not in blob
            assert "journal" not in blob
            for pmid in ("30099162", "30087819", "30010616"):
                assert pmid not in finding.retrieved_evidence
