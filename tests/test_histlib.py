# -*- coding: utf-8 -*-
"""
Tests for histlib (the shared hist.ini schema + rendering module).

Deliberately free of numpy/matplotlib so they run under both Python 2.7 (target)
and the local Python 3.8. Run with pytest, or directly:  python tests/test_histlib.py
"""

import os
import sys
import tempfile

# Make the scripts root importable regardless of where pytest is invoked from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import histlib


# A complete, canonical hist.ini body used by several tests.
CANONICAL_INI = (
    "[Path]\n"
    "data_dir = d\nfile_pattern = *.jav\noutput_dir = o\n"
    "[Plot]\n"
    "column = 3\nbins = 50\nx_min = 2\nx_max = 5\ny_min = 0\ny_max = 15000\ndpi = 200\n"
    "[Annotations]\n"
    "agn_name = Sim\ncomment =\nx_label = lag\ny_label = N\n"
    "lag_peak = 3.5\nlag_label = L\nlab_font_size = 14\ntitle_font_size = 16\n"
    "[Style]\n"
    "yaxis_right = True\nhist_color = #601fb4\nline_color = #ff0000\n"
)


def _write_tmp_ini(body):
    fd, path = tempfile.mkstemp(suffix=".ini")
    os.close(fd)
    with open(path, "w") as f:
        f.write(body)
    return path


class RecordingAx(object):
    """Minimal stand-in for a Matplotlib Axes that records method calls."""

    def __init__(self):
        self.calls = []

        class _YAxis(object):
            def __init__(self, calls):
                self._calls = calls

            def tick_right(self):
                self._calls.append("yaxis.tick_right")

            def set_label_position(self, pos):
                self._calls.append(("yaxis.set_label_position", pos))

        self.yaxis = _YAxis(self.calls)

    def __getattr__(self, name):
        def recorder(*args, **kwargs):
            self.calls.append((name, args, kwargs))
        return recorder


# --------------------------------------------------------------------------
# natural_sort_key
# --------------------------------------------------------------------------
def test_natural_sort_orders_numerically():
    names = ["javChain_1.jav", "javChain_10.jav", "javChain_2.jav"]
    ordered = sorted(names, key=histlib.natural_sort_key)
    assert ordered == ["javChain_1.jav", "javChain_2.jav", "javChain_10.jav"]


# --------------------------------------------------------------------------
# load_hist_config: types
# --------------------------------------------------------------------------
def test_load_config_types_and_values():
    path = _write_tmp_ini(CANONICAL_INI)
    try:
        cfg = histlib.load_hist_config(path)
    finally:
        os.remove(path)

    assert cfg["column"] == 3 and isinstance(cfg["column"], int)
    assert cfg["bins"] == 50 and isinstance(cfg["bins"], int)
    assert cfg["x_min"] == 2.0 and isinstance(cfg["x_min"], float)
    assert cfg["lag_peak"] == 3.5 and isinstance(cfg["lag_peak"], float)
    assert cfg["yaxis_right"] is True
    assert cfg["hist_color"] == "#601fb4"
    assert cfg["comment"] == ""  # empty value stays an empty string


def test_load_config_yaxis_false():
    body = CANONICAL_INI.replace("yaxis_right = True", "yaxis_right = False")
    path = _write_tmp_ini(body)
    try:
        cfg = histlib.load_hist_config(path)
    finally:
        os.remove(path)
    assert cfg["yaxis_right"] is False


# --------------------------------------------------------------------------
# load_hist_config: backward compatibility / defaults
# --------------------------------------------------------------------------
def test_legacy_data_column_number_fallback():
    body = (
        "[Path]\ndata_dir=d\nfile_pattern=*.jav\noutput_dir=o\n"
        "[Data]\ncolumn_number=5\n"
        "[Plot]\nbins=10\nx_min=1\nx_max=2\ny_min=0\ny_max=9\ndpi=100\n"
        "[Annotations]\nagn_name=A\ncomment=\nx_label=x\ny_label=y\n"
        "lag_peak=1.5\nlag_label=L\nlab_font_size=10\ntitle_font_size=12\n"
        "[Style]\nyaxis_right=False\n"
    )
    path = _write_tmp_ini(body)
    try:
        cfg = histlib.load_hist_config(path)
    finally:
        os.remove(path)
    # Column read from legacy [Data] column_number; colors default.
    assert cfg["column"] == 5
    assert cfg["hist_color"] == histlib.DEFAULT_HIST_COLOR
    assert cfg["line_color"] == histlib.DEFAULT_LINE_COLOR


def test_missing_column_defaults_to_three():
    body = (
        "[Path]\ndata_dir=d\nfile_pattern=*.jav\noutput_dir=o\n"
        "[Plot]\nbins=10\nx_min=1\nx_max=2\ny_min=0\ny_max=9\ndpi=100\n"
        "[Annotations]\nagn_name=A\ncomment=\nx_label=x\ny_label=y\n"
        "lag_peak=1\nlag_label=L\nlab_font_size=10\ntitle_font_size=12\n"
        "[Style]\nyaxis_right=False\n"
    )
    path = _write_tmp_ini(body)
    try:
        cfg = histlib.load_hist_config(path)
    finally:
        os.remove(path)
    assert cfg["column"] == 3


# --------------------------------------------------------------------------
# plot_histogram
# --------------------------------------------------------------------------
def test_plot_histogram_invokes_expected_axes_calls():
    path = _write_tmp_ini(CANONICAL_INI)
    try:
        cfg = histlib.load_hist_config(path)
    finally:
        os.remove(path)

    ax = RecordingAx()
    histlib.plot_histogram(ax, list(range(100)), cfg)

    names = [c[0] if isinstance(c, tuple) else c for c in ax.calls]
    for expected in ("hist", "set_xlim", "set_ylim", "axvline", "text",
                     "set_xlabel", "set_ylabel", "set_title"):
        assert expected in names
    # yaxis_right=True -> the right-axis calls must be present.
    assert "yaxis.tick_right" in names
    assert ("yaxis.set_label_position", "right") in ax.calls


def test_plot_histogram_skips_right_axis_when_disabled():
    body = CANONICAL_INI.replace("yaxis_right = True", "yaxis_right = False")
    path = _write_tmp_ini(body)
    try:
        cfg = histlib.load_hist_config(path)
    finally:
        os.remove(path)

    ax = RecordingAx()
    histlib.plot_histogram(ax, list(range(10)), cfg)
    names = [c[0] if isinstance(c, tuple) else c for c in ax.calls]
    assert "yaxis.tick_right" not in names


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
