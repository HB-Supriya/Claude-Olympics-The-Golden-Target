"""Output contract validation.

The harness parses the tool's entire stdout as one JSON value: a shape error scores the same as a
crash. So the contract is asserted in code, on every run, before anything is printed.
"""

from . import findings as findings_module

REQUIRED_TOP_LEVEL = ("unique_target_count", "golden_records", "findings")
REQUIRED_FINDING_FIELDS = ("gene", "observed", "correct", "retrieved_evidence", "evidence_source")
REQUIRED_RECORD_FIELDS = ("gene", "primary_accession", "sources")


class ContractError(ValueError):
    pass


def validate(payload):
    """Raise ``ContractError`` unless ``payload`` satisfies the published contract."""
    if not isinstance(payload, dict):
        raise ContractError("output must be a JSON object")
    for key in REQUIRED_TOP_LEVEL:
        if key not in payload:
            raise ContractError("missing required key %r" % key)

    count = payload["unique_target_count"]
    if isinstance(count, bool) or not isinstance(count, int):
        raise ContractError("unique_target_count must be an int, got %r" % type(count).__name__)

    records = payload["golden_records"]
    if not isinstance(records, list):
        raise ContractError("golden_records must be a JSON array")
    if count != len(records):
        raise ContractError(
            "unique_target_count (%d) must equal len(golden_records) (%d)" % (count, len(records))
        )

    seen = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ContractError("golden_records[%d] must be an object" % index)
        for field in REQUIRED_RECORD_FIELDS:
            if field not in record:
                raise ContractError("golden_records[%d] missing %r" % (index, field))
        if not isinstance(record["sources"], list):
            raise ContractError("golden_records[%d].sources must be an array" % index)
        accession = record["primary_accession"]
        if accession in seen:
            raise ContractError("duplicate primary_accession %r in golden_records" % accession)
        seen.add(accession)

    findings = payload["findings"]
    if not isinstance(findings, list):
        raise ContractError("findings must be a JSON array")
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise ContractError("findings[%d] must be an object" % index)
        for field in REQUIRED_FINDING_FIELDS:
            if not str(finding.get(field, "") or "").strip():
                # The rubric only awards full credit for a finding that carries its correction and
                # its proof, so an incomplete one is a bug, not something to ship quietly.
                raise ContractError("findings[%d] has empty %r" % (index, field))
        classification = finding.get("classification")
        if classification not in findings_module.REPORTABLE:
            # Fail here rather than publish a label the report never documented.
            raise ContractError(
                "findings[%d] has undocumented classification %r" % (index, classification)
            )
    return payload
