# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chains2hist


def test_chain_number_uses_last_integer():
    assert chains2hist.chain_number('javChain_7.jav', 0) == '7'
    assert chains2hist.chain_number('run2_javChain_13.jav', 0) == '13'


def test_chain_number_falls_back_to_index_plus_one():
    assert chains2hist.chain_number('nochain.jav', 4) == '5'


def _run_all():
    """Fallback runner so the file works without pytest installed."""
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS %s" % name)
            except AssertionError as e:
                failures += 1
                print("FAIL %s: %s" % (name, e))
    print("\n%s" % ("ALL PASSED" if failures == 0 else "%d FAILURE(S)" % failures))
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run_all() else 0)
