"""Load the five source extracts into a uniform row representation.

Each source names the same concepts differently (``accession`` / ``uniprot_id`` / ``uniprot_ref``;
``gene_symbol`` / ``gene_names``). Rather than scatter that knowledge through the detectors, every
row is mapped once here onto a common shape so downstream code reasons about *claims*, not columns.

The hidden pack is documented to share this schema, but column lookup is still tolerant (a small
set of aliases per field) so a harmless header variation cannot zero the run.
"""

import csv
import os

# Canonical source names, and the file each comes from.
SOURCE_FILES = (
    ("chembl", "source_chembl.csv"),
    ("uniprot", "source_uniprot.csv"),
    ("bindingdb", "source_bindingdb.csv"),
    ("internal", "source_internal.csv"),
    ("publications", "source_publications.csv"),
)

# Per source: canonical field -> candidate column names, most likely first.
FIELD_MAP = {
    "chembl": {
        "accession": ("accession", "uniprot_accession"),
        "gene_symbol": ("gene_symbol", "gene_name"),
        "protein_name": ("pref_name", "target_name", "protein_name"),
        "organism": ("organism", "species"),
        "tax_id": ("tax_id", "taxid", "tax_id_"),
        "chembl_id": ("chembl_id", "target_chembl_id"),
        "record_id": ("chembl_id",),
        "target_type": ("target_type",),
    },
    "uniprot": {
        "accession": ("accession", "primary_accession"),
        "gene_symbol": ("gene_names", "gene_symbol"),
        "protein_name": ("protein_name", "description"),
        "organism": ("organism", "species"),
        "entry_name": ("entry_name", "id"),
        "reviewed": ("reviewed",),
        "length": ("length",),
        "record_id": ("accession",),
    },
    "bindingdb": {
        "accession": ("uniprot_id", "accession"),
        "gene_symbol": ("gene_symbol", "gene_name"),
        "protein_name": ("target_name", "name"),
        "organism": ("species", "organism"),
        "record_id": ("uniprot_id",),
    },
    "internal": {
        "accession": ("uniprot_ref", "uniprot_id", "accession"),
        "gene_symbol": ("gene_symbol", "gene_name"),
        "protein_name": ("registered_name", "target_name"),
        "record_id": ("internal_id",),
        "external_id": ("external_id",),
        "source_db": ("source_db",),
        "status": ("status",),
    },
    "publications": {
        "gene_symbol": ("target_mention", "gene_symbol"),
        "context": ("context_sentence", "context"),
        "record_id": ("pmid",),
    },
}


class Row(object):
    """One row of one source extract, with its claims exposed under canonical names.

    ``raw`` is kept verbatim because findings must quote the defective value exactly "as it
    appears in the file".
    """

    __slots__ = ("source", "line_no", "raw", "_fields")

    def __init__(self, source, line_no, raw):
        self.source = source
        self.line_no = line_no
        self.raw = raw
        self._fields = {}
        for canonical, candidates in FIELD_MAP.get(source, {}).items():
            for column in candidates:
                if column in raw:
                    self._fields[canonical] = (raw.get(column) or "").strip()
                    break

    def get(self, field, default=""):
        return self._fields.get(field, default)

    @property
    def accession(self):
        return self.get("accession")

    @property
    def gene_symbol(self):
        return self.get("gene_symbol")

    @property
    def protein_name(self):
        return self.get("protein_name")

    @property
    def record_id(self):
        return self.get("record_id") or ("%s:line%d" % (self.source, self.line_no))

    def locator(self):
        """Human-readable pointer to this row, embedded in every finding for traceability."""
        return "%s.csv row %d (%s)" % (self.source_file_stem(), self.line_no, self.record_id)

    def source_file_stem(self):
        return "source_%s" % self.source

    def __repr__(self):
        return "<Row %s line=%d id=%s>" % (self.source, self.line_no, self.record_id)


def load_csv_rows(path, source):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for index, raw in enumerate(reader, start=2):  # start=2: line 1 is the header
            if not any((value or "").strip() for value in raw.values()):
                continue
            rows.append(Row(source, index, raw))
    return rows


def load_pack(pack_dir):
    """Return ``{source_name: [Row, ...]}`` for every extract present in ``pack_dir``."""
    pack = {}
    for source, filename in SOURCE_FILES:
        pack[source] = load_csv_rows(os.path.join(pack_dir, filename), source)
    return pack


def identity_rows(pack):
    """Rows that assert a protein identity (i.e. carry an accession).

    ``source_publications.csv`` is excluded: it carries free-text mentions, not accessions, and is
    handled by its own detector.
    """
    rows = []
    for source in ("chembl", "uniprot", "bindingdb", "internal"):
        rows.extend(pack.get(source, []))
    return rows
