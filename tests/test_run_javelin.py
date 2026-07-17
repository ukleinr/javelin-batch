# -*- coding: utf-8 -*-
import io
import os
import sys
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import run_javelin


def _good_settings():
    return {
        'cont_pattern': 'a', 'line_pattern': 'b',
        'chains_path': 'c', 'log_path': 'd',
        'n_walkers': 100, 'n_burn': 500, 'n_chain': 500,
        'lag_limit_min': 0.0, 'lag_limit_max': 10.0, 'n_iter': 50,
    }


def _write_cfg(text):
    fd, path = tempfile.mkstemp(suffix='.cfg')
    os.close(fd)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return path


def test_importing_module_leaves_stdout_intact():
    # Importing must NOT replace sys.stdout (that happens only inside main()).
    assert type(sys.stdout).__name__ != 'StreamToLogger'


def test_validate_settings_accepts_valid():
    run_javelin.validate_settings(_good_settings(), 'ok.cfg')


def test_validate_settings_rejects_inverted_lag():
    s = _good_settings()
    s['lag_limit_min'] = 5.0
    s['lag_limit_max'] = 5.0
    raised = False
    try:
        run_javelin.validate_settings(s, 'bad.cfg')
    except ValueError:
        raised = True
    assert raised


def test_load_config_reads_typed_values():
    path = _write_cfg(
        u"[paths]\n"
        u"cont_pattern = ../jav_data/*_cont*.dat\n"
        u"line_pattern = ../jav_data/*_line*.dat\n"
        u"chains_path = ../jav_data/chains_run1/\n"
        u"log_path = ../jav_data/logs/run1.log\n"
        u"[mcmc]\n"
        u"n_walkers = 100\nn_burn = 500\nn_chain = 500\n"
        u"lag_limit_min = 0\nlag_limit_max = 10\nn_iter = 50\n")
    try:
        s = run_javelin.load_config(path)
        assert s['n_walkers'] == 100
        assert s['lag_limit_max'] == 10.0
        assert s['cont_pattern'] == '../jav_data/*_cont*.dat'
    finally:
        os.remove(path)


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
