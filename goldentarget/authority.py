"""Resolution against the authoritative external source.

Primary authority: **EBI Proteins API** (``https://www.ebi.ac.uk/proteins/api/proteins``), which the
brief names as sufficient. It answers, for a live entry: what organism it belongs to, its approved
symbol, what other symbols it has been known by, and what it is cross-referenced to elsewhere.

It cannot answer one question, by design: what happened to an accession that no longer exists. A
merged, demerged or deleted accession simply does not come back from ``/proteins`` (and a
*secondary* accession comes back as an empty result, indistinguishable from a miss). For those we
escalate to **UniProt REST** (``https://rest.uniprot.org/uniprotkb``) — the same UniProt/EBI system
of record, a different endpoint of it — which returns ``inactiveReason`` with the merge target, and
redirects a secondary accession to its current primary. Every finding names whichever endpoint
actually produced its evidence.

Nothing here infers, guesses or hardcodes. A lookup either produces an authority answer or produces
nothing, so a detector can never assemble a finding out of thin air.
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor

from . import httpjson
from . import normalize
from .httpjson import encode_query

EBI_PROTEINS = "https://www.ebi.ac.uk/proteins/api/proteins"
UNIPROT_ENTRY = "https://rest.uniprot.org/uniprotkb/%s.json"
UNIPROT_SEARCH = "https://rest.uniprot.org/uniprotkb/search"

SRC_EBI = "EBI Proteins API GET /proteins?accession="
SRC_UNIPROT_ENTRY = "UniProt REST GET /uniprotkb/{accession}.json"
SRC_UNIPROT_SEARCH = "UniProt REST GET /uniprotkb/search?query="

# Batch size for the EBI accession query. Comfortably inside URL-length limits and the API's own
# practical ceiling, and turns ~640 accessions into ~8 round trips instead of ~640.
BATCH_SIZE = 80
MAX_WORKERS = 8
MAX_MERGE_DEPTH = 5

STATUS_ACTIVE = "active"
STATUS_SECONDARY = "secondary"
STATUS_MERGED = "merged"
STATUS_DEMERGED = "demerged"
STATUS_DELETED = "deleted"
STATUS_UNKNOWN = "unknown"


class ProteinRecord(object):
    """What the authority returned about one queried accession, in one uniform shape."""

    __slots__ = (
        "query", "status", "primary", "entry_name", "tax_id", "scientific_name", "common_names",
        "gene", "gene_synonyms", "protein_name", "protein_alt_names", "short_names",
        "secondary_accessions", "xrefs", "keywords", "comment_text", "merge_targets",
        "inactive_reason", "evidence", "evidence_source", "resolved_via", "isoform_ids",
    )

    def __init__(self, query, status=STATUS_UNKNOWN):
        self.query = query
        self.status = status
        self.primary = ""
        self.entry_name = ""
        self.tax_id = ""
        self.scientific_name = ""
        self.common_names = []
        self.gene = ""
        self.gene_synonyms = []
        self.protein_name = ""
        self.protein_alt_names = []
        self.short_names = []
        self.secondary_accessions = []
        self.xrefs = {}
        self.keywords = []
        self.comment_text = ""
        self.isoform_ids = {}
        self.merge_targets = []
        self.inactive_reason = ""
        self.evidence = ""
        self.evidence_source = ""
        self.resolved_via = []

    @property
    def is_live(self):
        return self.status in (STATUS_ACTIVE, STATUS_SECONDARY)

    @property
    def known(self):
        return self.status != STATUS_UNKNOWN

    def all_symbols(self):
        """Every symbol this entry legitimately answers to, per the authority."""
        symbols = set()
        for value in [self.gene] + list(self.gene_synonyms) + list(self.short_names):
            if value:
                symbols.add(normalize.upper(value))
        return symbols

    def all_names(self):
        names = [self.protein_name] + list(self.protein_alt_names) + list(self.short_names)
        return [n for n in names if n]

    def organism_label(self):
        if self.scientific_name and self.common_names:
            return "%s (%s)" % (self.scientific_name, self.common_names[0])
        return self.scientific_name or ""

    def describe(self):
        """Compact bag of authority text used to disambiguate a free-text mention."""
        parts = self.all_names() + [self.gene] + list(self.gene_synonyms) + list(self.keywords)
        if self.comment_text:
            parts.append(self.comment_text)
        return " ".join(p for p in parts if p)


def _first(seq, default=None):
    for item in seq or ():
        return item
    return default


def _parse_ebi_entry(entry):
    """Map an EBI Proteins API entry onto ``ProteinRecord``."""
    record = ProteinRecord(entry.get("accession", ""), STATUS_ACTIVE)
    record.primary = entry.get("accession", "")
    record.entry_name = entry.get("id", "") or ""

    organism = entry.get("organism") or {}
    record.tax_id = str(organism.get("taxonomy") or "")
    for name in organism.get("names") or ():
        if name.get("type") == "scientific":
            record.scientific_name = name.get("value", "")
        elif name.get("value"):
            record.common_names.append(name.get("value"))

    genes = entry.get("gene") or []
    primary_gene = _first(genes, {}) or {}
    record.gene = ((primary_gene.get("name") or {}).get("value") or "")
    for gene in genes:
        for synonym in gene.get("synonyms") or ():
            if synonym.get("value"):
                record.gene_synonyms.append(synonym["value"])
        # An entry may name the gene only via ORF/ordered-locus names.
        if not record.gene:
            for key in ("olnNames", "orfNames"):
                alt = _first(gene.get(key) or ())
                if alt and alt.get("value"):
                    record.gene = alt["value"]
                    break

    protein = entry.get("protein") or {}
    recommended = protein.get("recommendedName") or {}
    record.protein_name = (recommended.get("fullName") or {}).get("value", "") or ""
    for short in recommended.get("shortName") or ():
        if short.get("value"):
            record.short_names.append(short["value"])
    for alternative in protein.get("alternativeName") or ():
        full = (alternative.get("fullName") or {}).get("value")
        if full:
            record.protein_alt_names.append(full)
        for short in alternative.get("shortName") or ():
            if short.get("value"):
                record.short_names.append(short["value"])
    if not record.protein_name:
        submitted = _first(protein.get("submittedName") or ())
        if submitted:
            record.protein_name = (submitted.get("fullName") or {}).get("value", "") or ""

    record.secondary_accessions = list(entry.get("secondaryAccession") or ())

    for reference in entry.get("dbReferences") or ():
        db, identifier = reference.get("type"), reference.get("id")
        if db and identifier:
            record.xrefs.setdefault(db, []).append(identifier)

    record.keywords = [k.get("value", "") for k in (entry.get("keywords") or ()) if k.get("value")]
    comments = []
    for comment in entry.get("comments") or ():
        if comment.get("type") in ("FUNCTION", "SUBUNIT", "TISSUE_SPECIFICITY", "SIMILARITY", "CATALYTIC_ACTIVITY"):
            for text in comment.get("text") or ():
                if text.get("value"):
                    comments.append(text["value"])
        elif comment.get("type") == "ALTERNATIVE_PRODUCTS":
            # The entry's own list of splice variants. This is the proof that a row's "-n"
            # identifier is an isoform of this protein rather than a protein in its own right.
            for isoform in comment.get("isoforms") or ():
                for identifier in isoform.get("ids") or ():
                    label = (isoform.get("name") or {}).get("value") or ""
                    record.isoform_ids[normalize.upper(identifier)] = label
    record.comment_text = " ".join(comments)

    record.evidence = json.dumps(
        {
            "accession": record.primary,
            "id": record.entry_name,
            "organism": {"taxonomy": record.tax_id, "names": ([record.scientific_name] + record.common_names)},
            "gene": {"name": record.gene, "synonyms": record.gene_synonyms},
            "recommendedName": record.protein_name,
            "secondaryAccession": record.secondary_accessions,
        },
        sort_keys=True,
    )
    record.evidence_source = SRC_EBI + record.primary
    record.resolved_via = ["ebi-proteins"]
    return record


def _parse_uniprot_entry(queried, payload, final_url):
    """Map a UniProt REST entry (active, secondary-redirected, or inactive) onto ``ProteinRecord``."""
    record = ProteinRecord(queried)
    inactive = payload.get("inactiveReason") or {}
    primary = payload.get("primaryAccession", "") or ""
    record.entry_name = payload.get("uniProtkbId", "") or ""

    if inactive:
        reason = (inactive.get("inactiveReasonType") or "").upper()
        record.merge_targets = [a for a in (inactive.get("mergeDemergeTo") or ()) if a]
        record.inactive_reason = reason
        record.status = {
            "MERGED": STATUS_MERGED,
            "DEMERGED": STATUS_DEMERGED,
            "DELETED": STATUS_DELETED,
        }.get(reason, STATUS_UNKNOWN)
        record.evidence = json.dumps(
            {
                "entryType": payload.get("entryType"),
                "uniProtkbId": record.entry_name,
                "inactiveReason": {
                    "inactiveReasonType": reason,
                    "mergeDemergeTo": record.merge_targets,
                },
                "queried": queried,
                "redirectedTo": final_url,
            },
            sort_keys=True,
        )
        record.evidence_source = SRC_UNIPROT_ENTRY.replace("{accession}", queried)
        record.resolved_via = ["uniprot-rest"]
        return record

    record.primary = primary
    # UniProt redirects a secondary accession to its current primary entry; the differing
    # accession (and the "?from=" marker on the resolved URL) is the proof.
    record.status = STATUS_SECONDARY if (primary and primary != normalize.upper(queried)) else STATUS_ACTIVE

    organism = payload.get("organism") or {}
    record.tax_id = str(organism.get("taxonId") or "")
    record.scientific_name = organism.get("scientificName", "") or ""
    if organism.get("commonName"):
        record.common_names.append(organism["commonName"])

    genes = payload.get("genes") or []
    primary_gene = _first(genes, {}) or {}
    record.gene = ((primary_gene.get("geneName") or {}).get("value") or "")
    for gene in genes:
        for synonym in gene.get("synonyms") or ():
            if synonym.get("value"):
                record.gene_synonyms.append(synonym["value"])

    description = payload.get("proteinDescription") or {}
    recommended = description.get("recommendedName") or {}
    record.protein_name = (recommended.get("fullName") or {}).get("value", "") or ""
    for short in recommended.get("shortNames") or ():
        if short.get("value"):
            record.short_names.append(short["value"])
    for alternative in description.get("alternativeNames") or ():
        full = (alternative.get("fullName") or {}).get("value")
        if full:
            record.protein_alt_names.append(full)

    record.secondary_accessions = list(payload.get("secondaryAccessions") or ())
    for reference in payload.get("uniProtKBCrossReferences") or ():
        db, identifier = reference.get("database"), reference.get("id")
        if db and identifier:
            record.xrefs.setdefault(db, []).append(identifier)
    record.keywords = [k.get("name", "") for k in (payload.get("keywords") or ()) if k.get("name")]

    record.evidence = json.dumps(
        {
            "primaryAccession": record.primary,
            "uniProtkbId": record.entry_name,
            "entryType": payload.get("entryType"),
            "organism": {"scientificName": record.scientific_name, "taxonId": record.tax_id},
            "gene": {"name": record.gene, "synonyms": record.gene_synonyms},
            "resolvedFrom": queried,
            "resolvedUrl": final_url,
        },
        sort_keys=True,
    )
    record.evidence_source = SRC_UNIPROT_ENTRY.replace("{accession}", queried)
    record.resolved_via = ["uniprot-rest"]
    return record


class Authority(object):
    """Cached, batched, thread-safe façade over the two authority endpoints."""

    def __init__(self, client, verbose=False):
        self.client = client
        self.verbose = verbose
        self._records = {}
        self._symbol_cache = {}
        self._xref_cache = {}
        self._alias_cache = {}
        self._lock = threading.Lock()

    # ---------------------------------------------------------------- accessions

    def resolve_accessions(self, accessions):
        """Resolve every accession, following merge/demerge chains to a live entry.

        Returns ``{queried_accession: ProteinRecord}``. Chain targets are resolved too, so a
        caller can walk from a dead accession to the live entry it now denotes.
        """
        pending = sorted({normalize.upper(a) for a in accessions if normalize.upper(a)})
        for depth in range(MAX_MERGE_DEPTH):
            unresolved = [a for a in pending if a not in self._records]
            if not unresolved:
                break
            self._resolve_batch(unresolved)
            # Chain targets discovered this round become the next round's queries.
            next_round = []
            for accession in unresolved:
                record = self._records.get(accession)
                if record is not None:
                    for target in record.merge_targets:
                        target = normalize.upper(target)
                        if target and target not in self._records:
                            next_round.append(target)
            pending = sorted(set(next_round))
            if not pending:
                break
        return dict(self._records)

    def _resolve_batch(self, accessions):
        """One resolution round: EBI batch first, then per-accession UniProt for the leftovers."""
        batches = [accessions[i:i + BATCH_SIZE] for i in range(0, len(accessions), BATCH_SIZE)]
        found = {}

        def fetch_batch(batch):
            url = "%s?%s" % (EBI_PROTEINS, encode_query({"size": "-1", "accession": ",".join(batch)}))
            payload, _ = self.client.get_json(url)
            return payload if isinstance(payload, list) else []

        if batches:
            with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(batches))) as pool:
                for entries in pool.map(fetch_batch, batches):
                    for entry in entries:
                        if not isinstance(entry, dict) or not entry.get("accession"):
                            continue
                        record = _parse_ebi_entry(entry)
                        found[record.primary] = record

        with self._lock:
            for accession in accessions:
                if accession in found:
                    self._records[accession] = found[accession]

        # A batch omits anything that is not a live primary accession: obsolete entries and
        # secondary accessions both fall through here to the endpoint that can explain them.
        leftovers = [a for a in accessions if a not in found]
        if not leftovers:
            return

        def fetch_single(accession):
            # Redirects are deliberately not followed: UniProt answers an obsolete accession with a
            # 303 whose body is the inactive record (inactiveReason + mergeDemergeTo). Following it
            # would hand back the successor entry and throw away the reason.
            payload, final_url = self.client.get_json(
                UNIPROT_ENTRY % accession, follow_redirects=False
            )
            if payload is httpjson.UNREACHABLE:
                # We never reached the authority. Record nothing: an absent record reads as
                # "unresolved" downstream, whereas STATUS_UNKNOWN would assert non-existence and
                # manufacture an invalid_accession finding out of a timeout.
                return accession, None
            if not isinstance(payload, dict):
                # Reached the authority and it has no such entry: an unknown identifier.
                record = ProteinRecord(accession, STATUS_UNKNOWN)
                record.evidence_source = SRC_UNIPROT_ENTRY.replace("{accession}", accession)
                return accession, record
            return accession, _parse_uniprot_entry(accession, payload, final_url)

        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(leftovers))) as pool:
            for accession, record in pool.map(fetch_single, leftovers):
                if record is None:
                    continue
                with self._lock:
                    self._records[accession] = record

    def record(self, accession):
        return self._records.get(normalize.upper(accession))

    def canonical(self, accession):
        """Walk merge/demerge/secondary links to the live entry an accession now denotes.

        Returns ``(record_of_live_entry, chain)`` where ``chain`` lists every hop taken, so a
        finding can show its work. A demerge (one accession split into several) is ambiguous by
        nature and is left to the caller to disambiguate by gene symbol.
        """
        accession = normalize.upper(accession)
        chain = []
        seen = set()
        current = self.record(accession)
        while current is not None and current.query not in seen:
            seen.add(current.query)
            if current.status == STATUS_ACTIVE:
                return current, chain
            if current.status == STATUS_SECONDARY and current.primary:
                chain.append((current.query, STATUS_SECONDARY, current.primary))
                nxt = self.record(current.primary)
                if nxt is None or nxt.query in seen:
                    return current, chain
                current = nxt
                continue
            if current.status in (STATUS_MERGED, STATUS_DEMERGED) and current.merge_targets:
                if len(current.merge_targets) != 1:
                    return current, chain  # demerge: caller must choose
                target = normalize.upper(current.merge_targets[0])
                chain.append((current.query, current.status, target))
                nxt = self.record(target)
                if nxt is None or nxt.query in seen:
                    return current, chain
                current = nxt
                continue
            return current, chain
        return current, chain

    # ---------------------------------------------------------------- searches

    def find_by_symbol(self, symbol, tax_id=None):
        """Authoritative accessions for an exact gene symbol, reviewed entries preferred."""
        symbol = normalize.upper(symbol)
        if not symbol:
            return []
        key = (symbol, str(tax_id or ""))
        with self._lock:
            if key in self._symbol_cache:
                return self._symbol_cache[key]

        clauses = ["gene_exact:%s" % symbol]
        if tax_id:
            clauses.append("organism_id:%s" % tax_id)
        results = self._search("+AND+".join(clauses + ["reviewed:true"]))
        if not results:
            results = self._search("+AND+".join(clauses))
        with self._lock:
            self._symbol_cache[key] = results
        return results

    def find_by_alias(self, alias, tax_id=None):
        """Accessions answering to ``alias`` as approved symbol, synonym or short name.

        This is how an ambiguous literature mention is grounded: the authority itself tells us
        which entries legitimately share the alias.
        """
        alias = normalize.upper(alias)
        if not alias:
            return []
        key = (alias, str(tax_id or ""))
        with self._lock:
            if key in self._alias_cache:
                return self._alias_cache[key]
        clauses = ["(gene:%s+OR+protein_name:%s)" % (alias, alias)]
        if tax_id:
            clauses.append("organism_id:%s" % tax_id)
        results = self._search("+AND+".join(clauses + ["reviewed:true"]), size=25)
        with self._lock:
            self._alias_cache[key] = results
        return results

    def find_by_xref(self, database, identifier):
        """Which entry does an external database identifier belong to, per UniProt?"""
        database, identifier = (database or "").strip(), (identifier or "").strip()
        if not database or not identifier:
            return []
        key = (database.lower(), identifier.upper())
        with self._lock:
            if key in self._xref_cache:
                return self._xref_cache[key]
        results = self._search("xref:%s-%s" % (database.lower(), identifier))
        with self._lock:
            self._xref_cache[key] = results
        return results

    def prefetch_symbols(self, pairs):
        """Warm the symbol cache concurrently.

        ``detect_symbol`` walks rows one at a time, so left to itself it would issue its lookups
        serially — fine for a handful, but a pack with hundreds of symbol disagreements could spend
        most of the run waiting on round trips. Resolving the distinct (symbol, taxon) pairs up front
        in parallel keeps the detector's own loop purely local.
        """
        pending = sorted({
            (normalize.upper(symbol), str(tax_id or "")) for symbol, tax_id in pairs
            if normalize.upper(symbol)
        })
        pending = [p for p in pending if p not in self._symbol_cache]
        if not pending:
            return
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(pending))) as pool:
            list(pool.map(lambda p: self.find_by_symbol(p[0], p[1] or None), pending))

    def prefetch_xrefs(self, pairs):
        """Warm the cross-reference cache concurrently, for the same reason."""
        pending = sorted({
            ((database or "").lower(), (identifier or "").upper()) for database, identifier in pairs
            if database and identifier
        })
        pending = [p for p in pending if p not in self._xref_cache]
        if not pending:
            return
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(pending))) as pool:
            list(pool.map(lambda p: self.find_by_xref(p[0], p[1]), pending))

    def _search(self, query, size=10):
        url = "%s?%s" % (
            UNIPROT_SEARCH,
            encode_query(
                {
                    "query": query,
                    "fields": "accession,id,gene_names,protein_name,organism_name,organism_id,reviewed",
                    "format": "json",
                    "size": str(size),
                }
            ),
        )
        payload, _ = self.client.get_json(url)
        if not isinstance(payload, dict):
            return []
        hits = []
        for result in payload.get("results") or ():
            record = ProteinRecord(result.get("primaryAccession", ""), STATUS_ACTIVE)
            record.primary = result.get("primaryAccession", "")
            record.entry_name = result.get("uniProtkbId", "") or ""
            organism = result.get("organism") or {}
            record.tax_id = str(organism.get("taxonId") or "")
            record.scientific_name = organism.get("scientificName", "") or ""
            if organism.get("commonName"):
                record.common_names.append(organism["commonName"])
            genes = result.get("genes") or []
            primary_gene = _first(genes, {}) or {}
            record.gene = ((primary_gene.get("geneName") or {}).get("value") or "")
            for gene in genes:
                for synonym in gene.get("synonyms") or ():
                    if synonym.get("value"):
                        record.gene_synonyms.append(synonym["value"])
            description = result.get("proteinDescription") or {}
            recommended = description.get("recommendedName") or {}
            record.protein_name = (recommended.get("fullName") or {}).get("value", "") or ""
            for short in recommended.get("shortNames") or ():
                if short.get("value"):
                    record.short_names.append(short["value"])
            for alternative in description.get("alternativeNames") or ():
                full = (alternative.get("fullName") or {}).get("value")
                if full:
                    record.protein_alt_names.append(full)
            record.evidence = json.dumps(
                {
                    "primaryAccession": record.primary,
                    "uniProtkbId": record.entry_name,
                    "gene": {"name": record.gene, "synonyms": record.gene_synonyms},
                    "recommendedName": record.protein_name,
                    "organism": {"scientificName": record.scientific_name, "taxonId": record.tax_id},
                },
                sort_keys=True,
            )
            record.evidence_source = SRC_UNIPROT_SEARCH + query
            record.resolved_via = ["uniprot-search"]
            hits.append(record)
        return hits
