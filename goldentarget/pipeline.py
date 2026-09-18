"""Pipeline orchestration: pack in, contract-shaped result out.

Ordering matters and is not arbitrary:

1. **Resolve first.** Every distinct accession in the pack is resolved against the authority up
   front, in batches, so each identifier costs one lookup no matter how many rows repeat it.
2. **Detect row-level defects second.** These produce the accession corrections that clustering
   needs — a row whose accession points at the wrong protein must join the target it actually
   describes, or the wrong mapping quietly corrupts a golden record too.
3. **Cluster third**, on resolved identities rather than raw strings.
4. **Detect corpus-level defects last**, since duplicates and ambiguous mentions are only
   definable once the target set exists.
"""

import json
import os
import sys
import time

from . import contract, detectors, golden, normalize
from .authority import Authority
from .findings import drop_redundant_symbol_findings, merge_findings, restrict_to_contract
from .httpjson import Deadline, HttpJsonClient, JsonCache
from .loaders import identity_rows, load_pack

# The harness allows 5 minutes per pack. We stop network work well short of that so the report is
# always assembled and printed: a complete-but-partially-verified result beats a timeout, which
# scores zero.
DEFAULT_BUDGET_SECONDS = 240.0
NETWORK_FRACTION = 0.80


class Options(object):
    def __init__(self, budget=None, cache_path=None, use_cache=True, verbose=False,
                 cache_max_age_days=7.0):
        self.budget = float(budget or os.environ.get("GT_BUDGET_SECONDS") or DEFAULT_BUDGET_SECONDS)
        self.cache_path = cache_path
        self.use_cache = use_cache
        self.verbose = verbose
        self.cache_max_age_days = cache_max_age_days


def _log(options, message):
    if options.verbose:
        sys.stderr.write("[gt] %s\n" % message)


def accessions_to_resolve(rows):
    """Every accession worth asking the authority about.

    A value that is not shaped like a UniProtKB accession cannot be resolved by asking about it —
    the malformation is decidable locally, and querying it would only waste budget (or build a
    nonsense URL). Such rows are handled by ``detect_invalid_accession``, which repairs them from
    the gene symbol instead. Isoform identifiers are the one exception: they resolve through their
    parent entry, which is also the value the row should have carried.
    """
    accessions = set()
    for row in rows:
        value = normalize.upper(row.accession)
        if not value:
            continue
        if normalize.looks_like_accession(value):
            accessions.add(value)
            continue
        # An isoform identifier ("Q13422-3") is resolvable via its parent entry, which is also what
        # the row should have carried, so resolve the parent instead of discarding the row.
        split = normalize.split_isoform(value)
        if split:
            accessions.add(split[0])
    return sorted(accessions)


def _dominant_tax_id(clusters):
    """The taxon most of this pack's targets belong to.

    Used only to scope alias searches for literature mentions; it is derived from the data rather
    than assumed, so a non-human pack works identically.
    """
    counts = {}
    for cluster in clusters.values():
        record = cluster.get("record")
        if record is not None and record.tax_id:
            counts[record.tax_id] = counts.get(record.tax_id, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda item: item[1])[0]


def _prefetch_lookups(authority, rows, deadline, options):
    """Collect the symbol and cross-reference lookups the detectors will need, and warm them."""
    if not deadline.allows(NETWORK_FRACTION):
        return
    symbol_pairs = set()
    xref_pairs = set()
    for row in rows:
        symbol = normalize.upper(row.gene_symbol)
        record = authority.record(row.accession)
        if symbol:
            live = record
            if live is not None and live.is_live:
                # Only a symbol the accession does not already answer to needs resolving elsewhere.
                if symbol != normalize.upper(live.gene) and symbol not in live.all_symbols():
                    symbol_pairs.add((symbol, live.tax_id or None))
            elif record is not None and not record.known:
                symbol_pairs.add((symbol, row.get("tax_id") or None))
            elif record is None and row.accession:
                symbol_pairs.add((symbol, row.get("tax_id") or None))

        external = row.get("chembl_id") or row.get("external_id")
        if external and external.upper().startswith("CHEMBL"):
            live = authority.record(row.accession)
            listed = {v.upper() for v in (live.xrefs.get("ChEMBL", ()) if live is not None else ())}
            if listed and external.upper() not in listed:
                xref_pairs.add(("chembl", external))

    _log(options, "prefetching %d symbol and %d cross-reference lookups"
         % (len(symbol_pairs), len(xref_pairs)))
    authority.prefetch_symbols(symbol_pairs)
    authority.prefetch_xrefs(xref_pairs)


def run(pack_dir, options=None):
    """Reconcile ``pack_dir`` and return ``(payload, diagnostics)``."""
    options = options or Options()
    started = time.time()
    deadline = Deadline(options.budget)

    pack = load_pack(pack_dir)
    rows = identity_rows(pack)
    publication_rows = pack.get("publications", [])
    _log(options, "loaded %d identity rows, %d publication rows" % (len(rows), len(publication_rows)))

    cache = JsonCache(
        path=options.cache_path,
        max_age_days=options.cache_max_age_days,
        enabled=bool(options.use_cache and options.cache_path),
    )
    client = HttpJsonClient(deadline, cache=cache, verbose=options.verbose)
    authority = Authority(client, verbose=options.verbose)

    accessions = accessions_to_resolve(rows)
    _log(options, "resolving %d distinct accessions" % len(accessions))
    authority.resolve_accessions(accessions)
    _log(options, "resolution done at %.1fs (%s)" % (deadline.elapsed(), client.stats))

    # Warm the lookup caches concurrently before the detectors, which walk rows serially. Which
    # symbols/cross-references need checking is decidable locally from what the authority already
    # returned, so this costs nothing extra and removes a per-row round trip from the hot path.
    _prefetch_lookups(authority, rows, deadline, options)

    # ------------------------------------------------------------------ row-level detection
    raw_findings = []
    raw_findings.extend(detectors.detect_accession_status(authority, rows))
    raw_findings.extend(detectors.detect_isoform_accession(authority, rows))
    raw_findings.extend(detectors.detect_organism(authority, rows))
    if deadline.allows(NETWORK_FRACTION):
        raw_findings.extend(detectors.detect_invalid_accession(authority, rows))
    if deadline.allows(NETWORK_FRACTION):
        raw_findings.extend(detectors.detect_symbol(authority, rows))
    else:
        _log(options, "skipping symbol detection: network budget exhausted")
    if deadline.allows(NETWORK_FRACTION):
        raw_findings.extend(detectors.detect_crossreferences(authority, rows))
    else:
        _log(options, "skipping cross-reference detection: network budget exhausted")

    # A proven wrong or unusable accession must not also mis-file its row during clustering.
    corrections = {}
    for finding in raw_findings:
        if finding.field == "accession" and finding.classification in (
            "wrong_accession_mapping", "invalid_accession", "isoform_accession"
        ):
            for locator in finding.locations:
                corrections[locator] = finding.correct

    # Accessions whose duplication is already diagnosed as an obsolescence problem.
    explained = {
        finding.observed for finding in raw_findings
        if finding.classification in ("obsolete_accession", "secondary_accession")
    }

    # ------------------------------------------------------------------ clustering
    clusters = golden.build_clusters(authority, rows, corrections)
    _log(options, "clustered into %d targets" % len(clusters))

    # ------------------------------------------------------------------ corpus-level detection
    raw_findings.extend(detectors.detect_duplicates(authority, rows, clusters, explained=explained))

    mention_corrections = {}
    if publication_rows and deadline.allows(0.95):
        mention_findings = detectors.detect_ambiguous_mentions(
            authority, publication_rows, clusters, default_tax_id=_dominant_tax_id(clusters)
        )
        for finding in mention_findings:
            for locator in finding.locations:
                mention_corrections[locator] = finding.correct
        raw_findings.extend(mention_findings)

    # An obsolete key whose successor is independently present in the pack is *also* a duplicate
    # identity. Say so on the existing finding rather than emitting a second one.
    in_pack = set(clusters.keys())
    for finding in raw_findings:
        if finding.classification in ("obsolete_accession", "secondary_accession"):
            if normalize.upper(finding.correct) in in_pack:
                finding.impact += (
                    " The successor accession %s is also present in this pack, so the two together "
                    "form a duplicate identity for one protein." % finding.correct
                )

    golden.attach_publications(clusters, publication_rows, mention_corrections)

    # Withhold undocumented labels first, so a canonicalised accession defect is visible to the
    # redundancy pass that follows it.
    reportable, withheld = restrict_to_contract(raw_findings)
    if withheld:
        _log(options, "withheld undocumented classifications: %s" % json.dumps(withheld, sort_keys=True))
    reportable, redundant_symbols = drop_redundant_symbol_findings(reportable)
    if redundant_symbols:
        _log(options, "withheld %d stale-symbol findings on rows already reported for their accession"
             % redundant_symbols)

    findings = merge_findings(reportable)
    records = golden.golden_records(clusters)

    payload = {
        "unique_target_count": len(records),
        "golden_records": records,
        "findings": [finding.to_dict() for finding in findings],
    }
    contract.validate(payload)
    cache.flush()

    diagnostics = {
        "elapsed_seconds": round(time.time() - started, 2),
        "http": dict(client.stats),
        "identity_rows": len(rows),
        "publication_rows": len(publication_rows),
        "distinct_accessions": len(accessions),
        "clusters": len(clusters),
        "unverified_clusters": sum(1 for c in clusters.values() if not c["verified"]),
        "raw_findings": len(raw_findings),
        "reported_findings": len(findings),
        "budget_seconds": options.budget,
        "deadline_hit": deadline.expired(),
    }
    return payload, diagnostics
