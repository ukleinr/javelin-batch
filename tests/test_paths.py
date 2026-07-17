# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paths


def test_paths_are_absolute_and_named():
    assert os.path.isabs(paths.JAV_DATA)
    assert os.path.isabs(paths.LIGHT_CURVES)
    assert os.path.isabs(paths.RESULTS)
    assert paths.JAV_DATA.endswith('jav_data')
    assert paths.LIGHT_CURVES.endswith('light_curves')
    assert paths.RESULTS.endswith('results')


def test_paths_anchor_on_module_location_not_cwd():
    scripts_dir = os.path.dirname(os.path.abspath(paths.__file__))
    expected = os.path.normpath(os.path.join(scripts_dir, os.pardir, 'jav_data'))
    assert os.path.normpath(paths.JAV_DATA) == expected


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
