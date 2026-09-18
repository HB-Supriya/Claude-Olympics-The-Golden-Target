#!/usr/bin/env python3
"""
solve.py — Golden Target reconciliation tool.

Reconciles five source extracts (ChEMBL, UniProt, BindingDB, internal registry, literature
mentions) into one golden record per drug-discovery target, and flags real defects with proof
retrieved from the authoritative EBI Proteins API and UniProt REST endpoints.

Usage:
    python3 solve.py <pack_dir>

Prints exactly one JSON object to stdout — nothing else. All diagnostic output goes to stderr.
"""

import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from goldentarget.pipeline import Options, run


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: python3 solve.py <pack_dir>\n")
        sys.exit(2)

    pack_dir = sys.argv[1]
    if not os.path.isdir(pack_dir):
        sys.stderr.write("error: %s is not a directory\n" % pack_dir)
        sys.exit(2)

    cache_dir = os.path.join(HERE, ".gtcache")
    cache_path = os.environ.get("GT_CACHE_PATH") or os.path.join(cache_dir, "authority.json")
    verbose = os.environ.get("GT_VERBOSE", "").strip().lower() in ("1", "true", "yes", "on")

    try:
        options = Options(cache_path=cache_path, verbose=verbose)
        payload, diagnostics = run(pack_dir, options)
        print(json.dumps(payload))
        if verbose:
            sys.stderr.write("[gt] diagnostics: %s\n" % json.dumps(diagnostics))
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"unique_target_count": 0, "golden_records": [], "findings": []}))
        sys.exit(1)


if __name__ == "__main__":
    main()
