#!/usr/bin/env python3
"""Record authority responses for the mini pack so the test suite can run offline.

Tests must not depend on the network: a flaky endpoint should never look like a broken detector.
This script runs the real pipeline against ``tests/fixtures/mini_pack`` once, capturing every
request/response pair into a fixture the tests replay. Re-run it whenever the mini pack gains a
case, or to refresh the recording against the current state of the reference databases.

    python3 tools/record_fixtures.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from goldentarget.pipeline import Options, run  # noqa: E402

MINI_PACK = os.path.join(ROOT, "tests", "fixtures", "mini_pack")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "recorded_authority.json")


def main():
    options = Options(cache_path=FIXTURE, verbose=True, cache_max_age_days=36500.0)
    payload, diagnostics = run(MINI_PACK, options)
    sys.stderr.write("recorded %s\n" % FIXTURE)
    sys.stderr.write("targets=%d findings=%d http=%s\n" % (
        payload["unique_target_count"], len(payload["findings"]), diagnostics["http"],
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
