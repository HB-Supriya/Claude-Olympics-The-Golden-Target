#!/usr/bin/env python3
"""Generate the committed evidence artifacts for a pack.

    python3 tools/report.py [pack_dir]

Writes three files under ``reports/``:

* ``findings_<pack>.json`` — the tool's exact stdout, committed so every claim in the write-up is
  traceable to a machine-readable finding.
* ``findings_<pack>.md``   — the same findings as a readable audit trail: observed, corrected, the
  authority's literal answer, the endpoint, and which rows are affected.
* ``profile_<pack>.md``    — a structural profile of the pack (counts, key overlap, disagreements)
  produced *without* any external lookups, so the two halves of the audit stay separable: what the
  data says about itself, versus what the authority says about it.

This is a development/reporting utility. It is not part of the graded entry point.
"""

import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from goldentarget import normalize  # noqa: E402
from goldentarget.loaders import identity_rows, load_pack  # noqa: E402
from goldentarget.pipeline import Options, run  # noqa: E402

DEFAULT_PACK = os.path.join(ROOT, "golden-target-data", "exam")
REPORTS = os.path.join(ROOT, "reports")


def profile(pack_dir):
    """Structural profile: everything derivable from the files alone, with no network."""
    pack = load_pack(pack_dir)
    rows = identity_rows(pack)
    lines = ["# Data profile — `%s`" % os.path.basename(pack_dir.rstrip("/")), ""]
    lines.append("Derived from the files alone: no external lookups. This is the pass that decides")
    lines.append("*what to check*; the authority decides *what is wrong*.")
    lines.append("")

    lines.append("## Row counts")
    lines.append("")
    lines.append("| source | rows |")
    lines.append("|---|---|")
    for source in ("chembl", "uniprot", "bindingdb", "internal", "publications"):
        lines.append("| `source_%s.csv` | %d |" % (source, len(pack.get(source, []))))
    lines.append("")

    acc_to_genes = collections.defaultdict(set)
    acc_to_sources = collections.defaultdict(set)
    gene_to_accs = collections.defaultdict(set)
    blank_symbols = collections.Counter()
    malformed = collections.defaultdict(set)
    isoforms = collections.defaultdict(set)
    for row in rows:
        accession = normalize.upper(row.accession)
        if not accession:
            continue
        acc_to_sources[accession].add(row.source)
        if row.gene_symbol:
            acc_to_genes[accession].add(normalize.upper(row.gene_symbol))
            gene_to_accs[normalize.upper(row.gene_symbol)].add(accession)
        else:
            blank_symbols[row.source] += 1
        if not normalize.looks_like_accession(accession):
            if normalize.split_isoform(accession):
                isoforms[accession].add(row.source)
            else:
                malformed[accession].add(row.source)

    lines.append("## Identifier shape")
    lines.append("")
    lines.append("- distinct accession values: **%d**" % len(acc_to_sources))
    lines.append("- isoform-form values (`ACC-n`, valid but wrong granularity for a target): **%d** %s"
                 % (len(isoforms), sorted(isoforms) or ""))
    lines.append("- values that are not UniProtKB accessions at all: **%d** %s"
                 % (len(malformed), sorted(malformed) or ""))
    lines.append("- rows with a blank gene symbol: **%d** %s"
                 % (sum(blank_symbols.values()), dict(blank_symbols) or ""))
    lines.append("")

    conflicts = {a: g for a, g in acc_to_genes.items() if len(g) > 1}
    lines.append("## Internal disagreements (candidates to check against the authority)")
    lines.append("")
    lines.append("### One accession, several gene symbols — %d" % len(conflicts))
    lines.append("")
    if conflicts:
        lines.append("| accession | symbols claimed | sources |")
        lines.append("|---|---|---|")
        for accession, genes in sorted(conflicts.items()):
            lines.append("| `%s` | %s | %s |" % (
                accession, ", ".join(sorted(genes)), ", ".join(sorted(acc_to_sources[accession]))))
    lines.append("")

    multi = {g: a for g, a in gene_to_accs.items() if len(a) > 1}
    lines.append("### One gene symbol, several accessions — %d" % len(multi))
    lines.append("")
    if multi:
        lines.append("| gene | accessions |")
        lines.append("|---|---|")
        for gene, accessions in sorted(multi.items()):
            lines.append("| `%s` | %s |" % (gene, ", ".join(sorted(accessions))))
    lines.append("")

    lines.append("## Free-text spelling variation (normalized, never reported as a defect)")
    lines.append("")
    for source, field in (("chembl", "organism"), ("uniprot", "organism"), ("bindingdb", "organism")):
        counts = collections.Counter(r.get(field) for r in pack.get(source, []) if r.get(field))
        if counts:
            lines.append("- `source_%s.%s`: %s" % (
                source, field, ", ".join("%r×%d" % (v, c) for v, c in counts.most_common(6))))
    lines.append("")

    mentions = collections.Counter(r.gene_symbol for r in pack.get("publications", []) if r.gene_symbol)
    known_symbols = set(gene_to_accs)
    unknown = sorted(m for m in mentions if normalize.upper(m) not in known_symbols)
    lines.append("## Literature mentions")
    lines.append("")
    lines.append("- distinct mentions: **%d**" % len(mentions))
    lines.append("- mentions that are not the gene symbol of any target in this pack "
                 "(i.e. aliases needing resolution): **%d** %s" % (len(unknown), unknown or ""))
    lines.append("")
    lines.append("`pmid`, `journal` and `year` are deliberately not profiled and never fetched: they")
    lines.append("are internal reference numbers, and some collide with unrelated real PubMed records.")
    lines.append("")
    return "\n".join(lines)


def findings_markdown(payload, diagnostics, pack_dir):
    by_class = collections.Counter(f["classification"] for f in payload["findings"])
    by_severity = collections.Counter(f["severity"] for f in payload["findings"])
    lines = ["# Findings — `%s`" % os.path.basename(pack_dir.rstrip("/")), ""]
    lines.append("- unique targets: **%d**" % payload["unique_target_count"])
    lines.append("- findings reported: **%d** (from %d row-level detections, de-duplicated)"
                 % (len(payload["findings"]), diagnostics["raw_findings"]))
    lines.append("- by severity: %s" % ", ".join("%s=%d" % kv for kv in sorted(by_severity.items())))
    lines.append("- runtime: %.1fs, %d HTTP requests, %d errors"
                 % (diagnostics["elapsed_seconds"], diagnostics["http"]["requests"],
                    diagnostics["http"]["errors"]))
    lines.append("")
    lines.append("| # | severity | classification | count |")
    lines.append("|---|---|---|---|")
    for index, (name, count) in enumerate(by_class.most_common(), start=1):
        severity = next(f["severity"] for f in payload["findings"] if f["classification"] == name)
        lines.append("| %d | %s | `%s` | %d |" % (index, severity, name, count))
    lines.append("")

    for finding in payload["findings"]:
        lines.append("---")
        lines.append("")
        lines.append("### `%s` — %s (%s)" % (
            finding["classification"], finding.get("gene") or "?", finding["severity"]))
        lines.append("")
        lines.append("- **observed** (in file): `%s`" % finding["observed"])
        lines.append("- **correct** (per authority): `%s`" % finding["correct"])
        lines.append("- **field**: `%s`" % finding.get("field", "?"))
        lines.append("- **evidence_source**: `%s`" % finding["evidence_source"])
        lines.append("- **retrieved_evidence**:")
        lines.append("")
        lines.append("  ```")
        lines.append("  %s" % finding["retrieved_evidence"])
        lines.append("  ```")
        lines.append("")
        if finding.get("reasoning"):
            lines.append("- **why**: %s" % finding["reasoning"])
        if finding.get("impact"):
            lines.append("- **impact**: %s" % finding["impact"])
        if finding.get("locations"):
            lines.append("- **rows** (%d): %s" % (
                len(finding["locations"]),
                "; ".join("`%s`" % loc for loc in finding["locations"][:12])))
        lines.append("")
    return "\n".join(lines)


def main(argv):
    pack_dir = argv[1] if len(argv) > 1 else DEFAULT_PACK
    name = os.path.basename(pack_dir.rstrip("/")) or "pack"
    os.makedirs(REPORTS, exist_ok=True)

    profile_path = os.path.join(REPORTS, "profile_%s.md" % name)
    with open(profile_path, "w", encoding="utf-8") as fh:
        fh.write(profile(pack_dir))

    options = Options(cache_path=os.path.join(ROOT, ".gtcache", "authority.json"), verbose=True)
    payload, diagnostics = run(pack_dir, options)

    json_path = os.path.join(REPORTS, "findings_%s.json" % name)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")

    md_path = os.path.join(REPORTS, "findings_%s.md" % name)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(findings_markdown(payload, diagnostics, pack_dir))

    sys.stderr.write("wrote %s\n       %s\n       %s\n" % (profile_path, json_path, md_path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
