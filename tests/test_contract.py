"""Contract and end-to-end tests.

The harness parses this tool's entire stdout as one JSON value, and a shape error is scored exactly
like a crash. These tests cover the shape, the clustering behaviour that drives
``unique_target_count``, and the real subprocess invocation the harness performs.
"""

import json
import os
import subprocess
import sys

import pytest

from goldentarget import contract, golden
from goldentarget.contract import ContractError

from .stubs import MINI_PACK, resolved_offline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLVE = os.path.join(ROOT, "solve.py")


def valid_payload():
    return {
        "unique_target_count": 1,
        "golden_records": [{"gene": "PIM1", "primary_accession": "P11309", "sources": ["uniprot"]}],
        "findings": [],
    }


class TestContract(object):
    def test_valid_payload_passes(self):
        assert contract.validate(valid_payload())

    @pytest.mark.parametrize("key", ["unique_target_count", "golden_records", "findings"])
    def test_missing_top_level_key_fails(self, key):
        payload = valid_payload()
        del payload[key]
        with pytest.raises(ContractError):
            contract.validate(payload)

    def test_count_must_be_an_int_not_a_string(self):
        payload = valid_payload()
        payload["unique_target_count"] = "1"
        with pytest.raises(ContractError):
            contract.validate(payload)

    def test_count_must_match_record_total(self):
        payload = valid_payload()
        payload["unique_target_count"] = 99
        with pytest.raises(ContractError):
            contract.validate(payload)

    def test_duplicate_primary_accession_is_rejected(self):
        payload = valid_payload()
        payload["golden_records"].append(dict(payload["golden_records"][0]))
        payload["unique_target_count"] = 2
        with pytest.raises(ContractError):
            contract.validate(payload)

    def test_finding_without_correction_is_rejected(self):
        payload = valid_payload()
        payload["findings"] = [{
            "gene": "PIM1", "observed": "Q9P1W9", "correct": "",
            "retrieved_evidence": "x", "evidence_source": "y",
        }]
        with pytest.raises(ContractError):
            contract.validate(payload)


class TestClustering(object):
    def setup_method(self):
        self.authority, self.pack, self.rows = resolved_offline()

    def test_merged_and_successor_accessions_collapse_to_one_target(self):
        clusters = golden.build_clusters(self.authority, self.rows, {})
        # B5A968 was merged into P29317: one EPHA2 target, not two.
        assert "P29317" in clusters
        assert "B5A968" not in clusters

    def test_malformed_accession_creates_no_target_without_a_correction(self):
        from goldentarget import normalize
        clusters = golden.build_clusters(self.authority, self.rows, {})
        assert "P0521X" not in clusters
        for accession in clusters:
            assert normalize.looks_like_accession(accession), accession

    def test_isoform_row_is_keyed_on_its_parent_entry(self):
        clusters = golden.build_clusters(self.authority, self.rows, {})
        assert "Q13422" in clusters
        assert "Q13422-3" not in clusters

    def test_correction_files_a_row_under_the_target_it_describes(self):
        rows_by_id = {r.locator(): r for r in self.rows}
        chembl_pim1 = [loc for loc in rows_by_id if "CHEMBL2147" in loc][0]
        clusters = golden.build_clusters(self.authority, self.rows, {chembl_pim1: "P11309"})
        assert "chembl" in clusters["P11309"]["sources"]

    def test_golden_records_take_the_authority_symbol(self):
        clusters = golden.build_clusters(self.authority, self.rows, {})
        records = {r["primary_accession"]: r for r in golden.golden_records(clusters)}
        assert records["P78536"]["gene"] == "ADAM17"  # not the row's stale "CSVP"

    def test_publications_attach_as_provenance_but_create_no_target(self):
        # Corrections matter here: until the ChEMBL row that mis-files PIM1 under Q9P1W9 is
        # corrected, the symbol PIM1 points at two clusters and the mention is genuinely ambiguous.
        # That is the designed behaviour -- attach nothing rather than guess.
        rows_by_id = {r.locator(): r for r in self.rows}
        chembl_pim1 = [loc for loc in rows_by_id if "CHEMBL2147" in loc][0]
        clusters = golden.build_clusters(self.authority, self.rows, {chembl_pim1: "P11309"})
        before = set(clusters)
        golden.attach_publications(clusters, self.pack["publications"], {})
        assert set(clusters) == before, "publications must never create a target"
        records = {r["primary_accession"]: r for r in golden.golden_records(clusters)}
        assert "publications" in records["P11309"]["sources"]

    def test_ambiguous_mention_attaches_to_nothing(self):
        clusters = golden.build_clusters(self.authority, self.rows, {})
        golden.attach_publications(clusters, self.pack["publications"], {})
        # "PSA" is not the approved symbol of any target, so an unresolved mention adds no source.
        records = {r["primary_accession"]: r for r in golden.golden_records(clusters)}
        assert "publications" not in records["P07288"]["sources"]

    def test_resolved_mention_attaches_to_the_corrected_gene(self):
        clusters = golden.build_clusters(self.authority, self.rows, {})
        psa_row = [r.locator() for r in self.pack["publications"] if "30099162" in r.locator()][0]
        golden.attach_publications(clusters, self.pack["publications"], {psa_row: "KLK3"})
        records = {r["primary_accession"]: r for r in golden.golden_records(clusters)}
        assert "publications" in records["P07288"]["sources"]


class TestSubprocessInvocation(object):
    """Exercise the tool exactly as the harness does: a real process, one argument, stdout parsed."""

    def run_tool(self, pack_dir):
        env = dict(os.environ)
        env["GT_CACHE_PATH"] = os.path.join(ROOT, "tests", "fixtures", "recorded_authority.json")
        env["GT_BUDGET_SECONDS"] = "120"
        return subprocess.run(
            [sys.executable, SOLVE, pack_dir],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=300,
        )

    def test_stdout_is_exactly_one_json_object(self):
        result = self.run_tool(MINI_PACK)
        assert result.returncode == 0, result.stderr.decode()[-2000:]
        payload = json.loads(result.stdout.decode())  # no leading/trailing text tolerated
        contract.validate(payload)

    def test_findings_all_carry_observed_correct_and_proof(self):
        payload = json.loads(self.run_tool(MINI_PACK).stdout.decode())
        assert payload["findings"], "mini pack must surface defects"
        for finding in payload["findings"]:
            for field in ("observed", "correct", "retrieved_evidence", "evidence_source"):
                assert str(finding[field]).strip(), finding

    def test_every_defect_class_in_the_mini_pack_is_surfaced(self):
        payload = json.loads(self.run_tool(MINI_PACK).stdout.decode())
        classes = {f["classification"] for f in payload["findings"]}
        assert {
            "wrong_accession_mapping", "invalid_accession", "isoform_accession",
            "organism_mismatch", "obsolete_accession", "wrong_crossreference",
            "ambiguous_mention", "stale_gene_symbol", "missing_gene_symbol",
        } <= classes

    def test_missing_argument_is_an_error_not_a_crash(self):
        result = subprocess.run([sys.executable, SOLVE], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=60)
        assert result.returncode == 2

    def test_nonexistent_pack_directory_is_rejected(self):
        result = subprocess.run([sys.executable, SOLVE, "/no/such/pack"], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=60)
        assert result.returncode == 2

    def test_empty_pack_still_emits_valid_json(self, tmp_path):
        result = self.run_tool(str(tmp_path))
        assert result.returncode == 0, result.stderr.decode()[-2000:]
        payload = json.loads(result.stdout.decode())
        assert payload == {"unique_target_count": 0, "golden_records": [], "findings": []}
