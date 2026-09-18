"""Normalization tests.

These guard the precision boundary: everything asserted here is a difference the tool must treat as
cosmetic. If any of these started counting as a defect, the report would fill with false positives.
"""

from goldentarget import normalize


class TestOrganism(object):
    def test_all_spellings_of_one_organism_agree(self):
        for claimed in ("Homo sapiens", "H. sapiens", "human", "Human", "Homo sapiens (Human)",
                        "  homo   sapiens  "):
            assert normalize.organism_matches(
                claimed, "Homo sapiens", ["Human"], "9606", None
            ), claimed

    def test_genuine_cross_species_mismatch_is_not_excused(self):
        assert not normalize.organism_matches("Homo sapiens", "Mus musculus", ["Mouse"], "10090", None)
        assert not normalize.organism_matches("Rattus norvegicus", "Homo sapiens", ["Human"], "9606", None)

    def test_matching_tax_id_settles_it_regardless_of_spelling(self):
        assert normalize.organism_matches("whatever", "Homo sapiens", ["Human"], "9606", "9606")

    def test_conflicting_tax_id_does_not_rescue_a_mismatch(self):
        assert not normalize.organism_matches("Mus musculus", "Homo sapiens", ["Human"], "9606", "10090")

    def test_no_claim_cannot_contradict(self):
        assert normalize.organism_matches("", "Homo sapiens", ["Human"], "9606", None)

    def test_abbreviated_genus_expansion(self):
        assert normalize.expand_abbreviated_genus("H. sapiens") == ("h", "sapiens")
        assert normalize.expand_abbreviated_genus("Homo sapiens") is None


class TestNames(object):
    def test_hyphenation_and_casing_are_not_defects(self):
        assert normalize.names_agree("Prostate specific antigen", "Prostate-specific antigen")
        assert normalize.names_agree("srsf protein kinase 1", "SRSF protein kinase 1")

    def test_distinct_proteins_do_not_agree(self):
        assert not normalize.names_agree(
            "Serine/threonine-protein kinase pim-1", "Serine/threonine-protein kinase pim-2"
        )

    def test_empty_never_agrees(self):
        assert not normalize.names_agree("", "Prostate-specific antigen")


class TestAccessionGrammar(object):
    def test_accepts_real_accessions(self):
        for accession in ("P11309", "Q9P1W9", "A0A087WWS6", "O60226", "A6NNP5", "P0DJJ0"):
            assert normalize.looks_like_accession(accession), accession

    def test_rejects_non_accessions(self):
        for value in ("", "SINGLE PROTEIN", "P0521X", "CHEMBL2147", "PIM1", "P1130", "12345"):
            assert not normalize.looks_like_accession(value), value


class TestTokens(object):
    def test_stopwords_and_punctuation_are_dropped(self):
        assert "the" not in normalize.tokens("The kallikrein-family serine protease")
        assert "kallikrein" in normalize.tokens("The kallikrein-family serine protease")
