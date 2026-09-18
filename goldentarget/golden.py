"""Entity resolution and golden-record assembly.

The join key is deliberately *not* the accession string as written. Grouping on raw strings is what
produces two master records for one protein: a merged accession and its successor look like two
targets, and a row whose accession points at the wrong protein gets filed under that wrong protein.

So each row is first mapped to the **live entry the authority says it denotes**, applying, in order:
its merge/demerge/secondary chain, and any accession correction a detector proved. Rows then cluster
on that resolved identity, and the golden record takes its gene symbol and primary accession from
the authority rather than from a majority vote among sources that may all be wrong together.
"""

from collections import Counter

from . import normalize
from .detectors import terminal_identity


def resolved_accession_for(authority, row, corrections):
    """The live accession a row denotes, or its raw accession when nothing better is provable.

    ``corrections`` maps a row locator to an accession a detector proved to be the right one, so a
    wrong-mapping row joins the target it actually describes instead of the one it named.
    """
    raw = normalize.upper(row.accession)
    if not raw:
        return "", False

    corrected = corrections.get(row.locator())
    if corrected:
        raw = normalize.upper(corrected)
    elif not normalize.looks_like_accession(raw):
        split = normalize.split_isoform(raw)
        parent = authority.record(split[0]) if split else None
        if parent is not None and parent.is_live:
            # An isoform identifier still tells us which protein the row is about, so the target is
            # kept and keyed on the parent entry even if the isoform detector could not confirm it.
            raw = normalize.upper(split[0])
        else:
            # A malformed value can never be a primary accession. Without a proven correction there
            # is nothing to key a golden record on, so the row contributes no target rather than
            # inventing one out of a typo.
            return "", False

    record = authority.record(raw)
    if record is None or not record.known:
        return raw, False  # keep the target, but mark it unverified rather than dropping it

    final, _, live = terminal_identity(authority, row, raw)
    if live is not None and live.is_live and live.primary:
        return normalize.upper(live.primary), True
    return final or raw, bool(final and final != raw)


def build_clusters(authority, rows, corrections):
    """Group identity-bearing rows onto one cluster per real target."""
    clusters = {}
    for row in rows:
        accession, verified = resolved_accession_for(authority, row, corrections)
        if not accession:
            continue
        cluster = clusters.get(accession)
        if cluster is None:
            cluster = clusters[accession] = {
                "accession": accession,
                "record": authority.record(accession),
                "verified": False,
                "rows": [],
                "sources": set(),
                "raw_accessions": set(),
                "locations_by_accession": {},
                "sources_by_accession": {},
                "symbols": Counter(),
            }
        cluster["rows"].append(row)
        cluster["sources"].add(row.source)
        cluster["verified"] = cluster["verified"] or verified
        raw = normalize.upper(row.accession)
        # A row whose accession a detector *corrected* does not evidence a second identity for this
        # target -- it was simply pointing at the wrong protein, which is already reported as a
        # wrong mapping. Counting it here would double-report the same defect as a duplicate too.
        if raw and not corrections.get(row.locator()):
            cluster["raw_accessions"].add(raw)
            cluster["locations_by_accession"].setdefault(raw, set()).add(row.locator())
            cluster["sources_by_accession"].setdefault(raw, set()).add(row.source_file_stem())
        if row.gene_symbol:
            cluster["symbols"][normalize.upper(row.gene_symbol)] += 1
        if cluster["record"] is None:
            cluster["record"] = authority.record(accession)
    return clusters


def attach_publications(clusters, publication_rows, mention_corrections):
    """Credit the literature table as a source for targets it attests.

    ``source_publications.csv`` is one of the five extracts being reconciled, so a target it
    mentions is attested by it and that provenance belongs in the golden record. Mentions are
    matched on the authority's approved symbol, using the corrected gene where a mention was
    ambiguous and the context sentence resolved it.

    Publications never *create* a target: the file carries no accession, so a mention with no
    counterpart in the other four extracts cannot be given a primary accession and is left out of
    the count rather than guessed at.
    """
    by_symbol = {}
    for accession, cluster in clusters.items():
        record = cluster.get("record")
        symbols = set(cluster["symbols"])
        if record is not None and record.gene:
            symbols.add(normalize.upper(record.gene))
        for symbol in symbols:
            # A set, not a list: the same accession reached via both its authority symbol and a
            # source symbol must not look like two competing targets for one mention.
            by_symbol.setdefault(symbol, set()).add(accession)

    attached = 0
    for row in publication_rows:
        mention = mention_corrections.get(row.locator()) or row.gene_symbol
        if not mention:
            continue
        matches = by_symbol.get(normalize.upper(mention)) or set()
        if len(matches) != 1:
            continue  # ambiguous or absent: attach nothing rather than guess
        clusters[next(iter(matches))]["sources"].add("publications")
        attached += 1
    return attached


def golden_records(clusters):
    """One golden record per cluster: authority-chosen gene and accession, plus provenance."""
    records = []
    for accession in sorted(clusters):
        cluster = clusters[accession]
        record = cluster.get("record")
        gene = ""
        if record is not None and record.gene:
            gene = record.gene  # the authority's approved symbol, not a vote among sources
        elif cluster["symbols"]:
            gene = cluster["symbols"].most_common(1)[0][0]
        records.append({
            "gene": gene,
            "primary_accession": accession,
            "sources": sorted(cluster["sources"]),
        })
    return records
