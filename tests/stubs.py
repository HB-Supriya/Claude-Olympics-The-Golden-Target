"""Test helpers: offline replay of recorded authority responses.

Tests must never touch the network. A flaky endpoint should look like a flaky endpoint, not like a
broken detector, and the whole suite has to run in CI without external access. So tests build a real
:class:`Authority` on top of a client that serves only the recorded fixture and *fails loudly* on any
request that was not recorded — which also means a change that starts issuing new lookups cannot
silently slip past the suite.
"""

import os

from goldentarget.httpjson import Deadline, JsonCache

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDED = os.path.join(FIXTURE_DIR, "fixtures", "recorded_authority.json")
MINI_PACK = os.path.join(FIXTURE_DIR, "fixtures", "mini_pack")


class UnexpectedRequest(AssertionError):
    """Raised when a test would have hit the network."""


class OfflineClient(object):
    """Replays recorded responses; refuses to make real requests."""

    def __init__(self, recorded_path=RECORDED, strict=True):
        # A very long max age: the fixture is a recording, not a cache to be expired.
        self.cache = JsonCache(path=recorded_path, max_age_days=36500.0, enabled=True)
        self.strict = strict
        self.deadline = Deadline(600)
        self.stats = {"requests": 0, "cache_hits": 0, "errors": 0, "not_found": 0, "retries": 0}
        self.misses = []

    def get_json(self, url, allow_not_found=True, follow_redirects=True):
        key = url if follow_redirects else url + "#noredirect"
        entry = self.cache.get(key)
        if entry is None:
            self.misses.append(key)
            if self.strict:
                raise UnexpectedRequest(
                    "test attempted an un-recorded request: %s\n"
                    "Re-run tools/record_fixtures.py if the mini pack changed." % key
                )
            return None, url
        self.stats["cache_hits"] += 1
        return entry.get("payload"), entry.get("status") or url


def offline_authority(strict=True):
    from goldentarget.authority import Authority

    return Authority(OfflineClient(strict=strict))


def resolved_offline(pack_dir=MINI_PACK, strict=True):
    """Load a pack and resolve it offline, using the pipeline's own accession selection.

    Tests deliberately reuse ``accessions_to_resolve`` rather than re-deriving which identifiers to
    look up; a test that resolved a different set from the tool would not be testing the tool.
    """
    from goldentarget.loaders import identity_rows, load_pack
    from goldentarget.pipeline import accessions_to_resolve

    authority = offline_authority(strict=strict)
    pack = load_pack(pack_dir)
    rows = identity_rows(pack)
    authority.resolve_accessions(accessions_to_resolve(rows))
    return authority, pack, rows
