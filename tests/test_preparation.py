# -*- coding: utf-8 -*-
import io
import os
import sys
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import preparation


def _write_txt(text):
    fd, path = tempfile.mkstemp(suffix='.txt')
    os.close(fd)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return path


def test_convert_strips_comments_blanks_and_counts_bad_rows():
    txt = _write_txt(u"# header\n\n1.0 2.0 0.1\n3.0 4.0\n5.0 x 0.2\n")
    fd, dat = tempfile.mkstemp(suffix='.dat')
    os.close(fd)
    try:
        n_data, n_bad = preparation.convert_light_curve(txt, dat)
        assert n_data == 3          # three non-comment, non-blank rows
        assert n_bad == 2           # 2-column row + non-numeric row
        with io.open(dat, 'r', encoding='utf-8') as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        assert lines == [u'1.0 2.0 0.1', u'3.0 4.0', u'5.0 x 0.2']
    finally:
        os.remove(txt)
        os.remove(dat)


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
