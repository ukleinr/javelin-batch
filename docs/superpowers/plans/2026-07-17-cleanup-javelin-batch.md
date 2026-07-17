# Cleanup javelin-batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pay down legacy hygiene debt in the JAVELIN batch scripts (packaging, naming, path robustness, test coverage) without changing pipeline behavior or the Python 2.7 target.

**Architecture:** Keep the flat script-set layout (the repo *is* the object's `scripts/` folder). Add a `.gitignore` and `requirements.txt`, rename hyphenated files to importable identifiers, introduce a `paths.py` module that anchors data dirs on its own `__file__` (not CWD), extract testable functions out of the two flat scripts (`preparation.py`, `run_javelin.py` stdout hijack), and grow the pytest suite beyond `histlib`.

**Tech Stack:** Python 2.7 (target runtime), numpy, matplotlib, Tkinter (GUI only), pytest (dev), JAVELIN v0.33 (external, lazily imported).

## Global Constraints

- **Python 2.7 only.** Target runtime; keep Py2/3 shims as insurance but 2.7 is canonical. Use Py2 idioms (`ConfigParser`, `io.open`, `.format()`, no f-strings).
- **The repo IS `scripts/`.** Deployed as `object1/scripts/`; data dirs are siblings (`../jav_data`, `../light_curves`, `../results`). **Never create a `scripts/` subdirectory** — it double-nests and breaks every relative path.
- **Do not change contracts:** `.cfg` schema, `hist.ini` schema, `.dat`/`.jav` formats, lag-column-3 convention, and the MCMC contract (`Cont_Model.hpd` → `Pmap_Model.do_mcmc(conthpd=..., laglimit=[[min,max]])`) stay untouched.
- **`paths.py` does not rewrite cfg-internal globs.** Patterns inside user `.cfg`/`hist.ini` files stay CWD-relative and user-owned.
- **`histlib` must not import Tkinter at module level** (keeps `chains2hist.py` headless).
- **Shims are ConfigParser-first everywhere** (Python-2 name first, `configparser` as fallback).
- **Commits:** Conventional Commits, English, imperative, ≤72 chars. No `Co-Authored-By`/`Generated with` trailers.

## Testing Protocol (overrides every `pytest` command below)

The target image `ub18-jav:latest` has **no pytest**, and the host Python (3.14) is too new (`SafeConfigParser` removed). Therefore:

- **Run tests only inside the target image**, from the repo root, per test file:
  `MSYS_NO_PATHCONV=1 docker run --rm -v "G:\5-dev\github\javelin-batch:/repo" -w /repo ub18-jav:latest python2 tests/<file>.py`
  Wherever a step says `python -m pytest tests/<file>.py`, run the docker command above instead. "Expected: FAIL/PASS" still applies (the manual runner prints `PASS <name>` / `FAIL <name>` and a final `ALL PASSED`).
- **Every new test file must be self-contained** (no `conftest.py` / pytest dependency): include the sys.path bootstrap at the top and the `_run_all()` runner at the bottom, mirroring `tests/test_histlib.py`.

Top bootstrap (first lines of every new test file, after the encoding comment):
```python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

Bottom runner (last lines of every new test file):
```python
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
```

---

### Task 1: Repo hygiene & dependency manifest

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Remove: `__pycache__/histlib.cpython-38.pyc` (and the `__pycache__/` dir)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing importable; foundation only.

- [ ] **Step 1: Write `.gitignore`**

```gitignore
# Byte-compiled
__pycache__/
*.py[cod]
*.egg-info/

# Generated pipeline artifacts (data dirs normally live outside the repo)
*.dat
*.jav
*.png
/jav_data/
/results/

# OS / editor cruft
.DS_Store
Thumbs.db
*.swp
```

- [ ] **Step 2: Write `requirements.txt`**

```text
# Python 2.7 target (JAVELIN v0.33, Ubuntu 18.04). Last releases supporting 2.7.
# Verified against the ub18-jav:latest image (2026-07-17): Python 2.7.17,
# numpy 1.16.6, matplotlib 2.2.5.
numpy==1.16.6
matplotlib==2.2.5
# Tkinter is stdlib (OS package `python-tk`), not pip-installable.
# javelin is external and built with a Fortran compiler:
# javelin @ git+https://github.com/nye17/javelin.git@0.33
```

- [ ] **Step 3: Remove the stray bytecode**

Run: `git rm -r --cached --ignore-unmatch __pycache__ && rm -rf __pycache__`
Expected: `__pycache__/` gone from the working tree; nothing was tracked, so no staged deletion beyond cache clear.

- [ ] **Step 4: Commit**

```bash
git add .gitignore requirements.txt
git commit -m "chore: add gitignore and pinned py2.7 requirements"
```

---

### Task 2: Rename files to importable identifiers + sync docs

Renames break the documented run commands, so docs update in the same task.

**Files:**
- Rename: `run-javelin.py` → `run_javelin.py`
- Rename: `hist-tuner.py` → `hist_tuner.py`
- Rename: `utilites/` → `utilities/` (with `lc_gen.py`, `lc_plot.py`)
- Modify: `README.md`, `readme-ru.md`, `QUICKSTART.md`, `CLAUDE.md`

**Interfaces:**
- Consumes: nothing.
- Produces: modules `run_javelin`, `hist_tuner` are now importable by name; `utilities/` is correctly spelled.

- [ ] **Step 1: Rename via git (preserves history)**

Run:
```bash
git mv run-javelin.py run_javelin.py
git mv hist-tuner.py hist_tuner.py
git mv utilites utilities
```
Expected: three renames staged; no content change yet.

- [ ] **Step 2: Update run commands & file listings in docs**

In `README.md`, `readme-ru.md`, `QUICKSTART.md`, `CLAUDE.md`, replace every occurrence:
- `run-javelin.py` → `run_javelin.py`
- `hist-tuner.py` → `hist_tuner.py`
- `utilites` → `utilities`

- [ ] **Step 3: Verify no stale references remain**

Run: `grep -rn -e 'run-javelin' -e 'hist-tuner' -e 'utilites' . --include='*.md' --include='*.py'`
Expected: no matches.

- [ ] **Step 4: Verify existing tests still pass**

Run: `python -m pytest tests/ -q`
Expected: PASS (test_histlib unaffected by renames).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: rename hyphenated scripts and utilites dir, sync docs"
```

---

### Task 3: Shared `paths.py` module

**Files:**
- Create: `paths.py`
- Create: `tests/test_paths.py`

**Interfaces:**
- Produces: `paths.OBJECT_DIR`, `paths.JAV_DATA`, `paths.LIGHT_CURVES`, `paths.RESULTS` — absolute path strings anchored on `paths.__file__`.

Note: `tests/test_histlib.py` keeps its own `sys.path` bootstrap (no `conftest.py`, since the image has no pytest — see Testing Protocol). `test_paths.py` is self-contained the same way.

- [ ] **Step 1: Write the failing test `tests/test_paths.py`**

Include the top bootstrap and bottom `_run_all()` runner from the Testing Protocol. Test bodies:

```python
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
```

- [ ] **Step 2: Run test to verify it fails** (see Testing Protocol for the docker command)

Run: `... python2 tests/test_paths.py`
Expected: FAIL — `ImportError: No module named paths`.

- [ ] **Step 3: Write `paths.py`**

```python
# -*- coding: utf-8 -*-
"""Object-relative data paths, anchored on this module's location.

Resolves the object's data directories from this file's location rather than
the process CWD, so pipeline scripts work regardless of where they are invoked
while still resolving to the same tree in normal use (run from ``scripts/``).
Must stay Python 2.7 compatible.
"""
import os

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
OBJECT_DIR = os.path.dirname(_SCRIPTS_DIR)

JAV_DATA = os.path.join(OBJECT_DIR, 'jav_data')
LIGHT_CURVES = os.path.join(OBJECT_DIR, 'light_curves')
RESULTS = os.path.join(OBJECT_DIR, 'results')
```

- [ ] **Step 4: Run test to verify it passes**

Run: `... python2 tests/test_paths.py`
Expected: PASS (`ALL PASSED`).

- [ ] **Step 5: Commit**

```bash
git add paths.py tests/test_paths.py
git commit -m "feat: add cwd-independent paths module"
```

---

### Task 4: Make `run_javelin.py` import-safe + testable + wire paths

The stdout/stderr hijack currently runs at import time (`run_javelin.py:126-128`), so the module cannot be imported by tests. Move it into `main()`, flip the ConfigParser shim to Py2-first, and route `config_dir` through `paths`.

**Files:**
- Modify: `run_javelin.py` (shim ~48-51; stdout hijack ~126-128; `main` `config_dir` ~280)
- Create: `tests/test_run_javelin.py`

**Interfaces:**
- Consumes: `paths.LIGHT_CURVES`.
- Produces: importable `run_javelin.load_config(config_path) -> dict`, `run_javelin.validate_settings(settings, config_name) -> None` (raises `ValueError`).

- [ ] **Step 1: Write the failing test `tests/test_run_javelin.py`**

```python
# -*- coding: utf-8 -*-
import io
import os
import tempfile

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


def test_validate_settings_accepts_valid():
    run_javelin.validate_settings(_good_settings(), 'ok.cfg')  # must not raise


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_run_javelin.py -q`
Expected: FAIL — importing `run_javelin` today hijacks stdout at module load (breaks capture) / module not import-safe.

- [ ] **Step 3: Flip the ConfigParser shim to Py2-first**

Replace `run_javelin.py:48-51`:
```python
try:
    import ConfigParser as configparser  # Python 2 (target runtime)
except ImportError:
    import configparser  # Python 3 fallback (insurance, not a supported target)
```

- [ ] **Step 4: Move the stdout/stderr hijack out of module top-level**

Delete `run_javelin.py:126-128` (the three lines assigning `sys.stdout`/`sys.stderr = StreamToLogger(...)`). Add a helper right after `print_progress`:
```python
def _redirect_streams_to_logger():
    """Route stray library prints into the logger. Called from main() only, so
    importing this module (e.g. in tests) leaves sys.stdout/stderr intact."""
    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)
```
Then call it as the first line inside `main()`:
```python
def main():
    """Main function: finds all .cfg files and processes them sequentially."""
    _redirect_streams_to_logger()

    config_dir = paths.LIGHT_CURVES
    ...
```

- [ ] **Step 5: Import `paths` and use it for `config_dir`**

Add near the other imports:
```python
import paths
```
Confirm `main()` now sets `config_dir = paths.LIGHT_CURVES` (from Step 4). The `finally` block at `__main__` still restores `sys.stdout/stderr` — leave it unchanged.

- [ ] **Step 6: Run test to verify it passes**

Run: `python -m pytest tests/test_run_javelin.py -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add run_javelin.py tests/test_run_javelin.py
git commit -m "refactor: make run_javelin import-safe, test config/validation"
```

---

### Task 5: Refactor `preparation.py` into functions + wire paths + test

`preparation.py` is a flat script; extract behavior-preserving functions so the cleaning logic is testable, and route dirs through `paths`.

**Files:**
- Modify: `preparation.py` (whole file → functions + `main()` guard)
- Create: `tests/test_preparation.py`

**Interfaces:**
- Consumes: `paths.LIGHT_CURVES`, `paths.JAV_DATA`, `paths.RESULTS`.
- Produces: `preparation.convert_light_curve(txt_path, dat_path) -> (n_data, n_bad)`; `preparation.ensure_dirs(dirs) -> None`; `preparation.main() -> None`.

- [ ] **Step 1: Write the failing test `tests/test_preparation.py`**

```python
# -*- coding: utf-8 -*-
import io
import os
import tempfile

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_preparation.py -q`
Expected: FAIL — `preparation.py` runs its directory setup at import and has no `convert_light_curve`.

- [ ] **Step 3: Rewrite `preparation.py` as functions**

Replace the module body (keep the header docstring and imports; add `import paths`) with:
```python
import os
import io
import paths

DEFAULT_CONFIG = u"""[paths]
cont_pattern = ../jav_data/*_cont*.dat
line_pattern = ../jav_data/*_line*.dat
chains_path = ../jav_data/chains_run1/
log_path = ../jav_data/logs/run1.log

[mcmc]
n_walkers = 100
n_burn = 500
n_chain = 500
lag_limit_min = 0
lag_limit_max = 10
n_iter = 50
"""


def ensure_dirs(dirs):
    """Create each directory if missing."""
    for d in dirs:
        if not os.path.exists(d):
            try:
                os.makedirs(d)
                print("Created: {}".format(d))
            except Exception as e:
                print("Error creating {}: {}".format(d, e))
        else:
            print("Exists:  {}".format(d))


def write_default_config(config_path, content):
    """Write the default cfg only when absent."""
    if not os.path.exists(config_path):
        try:
            with io.open(config_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("Created default config: {}".format(config_path))
        except Exception as e:
            print("Error creating config: {}".format(e))
    else:
        print("Config already exists: {}".format(config_path))


def convert_light_curve(txt_path, dat_path):
    """Strip comments/blank lines, write cleaned rows, return (n_data, n_bad).

    n_data counts non-comment, non-blank rows; n_bad counts those that are not
    exactly three numeric columns (MJD, flux, error). Bad rows are still
    written, matching the original behavior.
    """
    n_data = 0
    n_bad = 0
    with io.open(txt_path, "r", encoding="utf-8") as f_in, \
            io.open(dat_path, "w", encoding="utf-8", newline=u"\n") as f_out:
        for line in f_in:
            line = line.strip()
            if not line or line.startswith(u"#"):
                continue
            cols = line.split()
            n_data += 1
            if len(cols) != 3:
                n_bad += 1
            else:
                try:
                    [float(c) for c in cols]
                except ValueError:
                    n_bad += 1
            f_out.write(line + u"\n")
    return n_data, n_bad


def main():
    import glob

    input_dir = paths.LIGHT_CURVES
    output_dir = paths.JAV_DATA
    dirs_to_ensure = [
        paths.JAV_DATA,
        os.path.join(paths.JAV_DATA, "_sessions"),
        paths.RESULTS,
        os.path.join(paths.RESULTS, "_sessions"),
        paths.LIGHT_CURVES,
        os.path.join(paths.LIGHT_CURVES, "_versions"),
    ]

    print("--- Initializing Directory Structure ---")
    ensure_dirs(dirs_to_ensure)

    print("\n--- Checking Configuration Files ---")
    write_default_config(os.path.join(input_dir, "start1.cfg"), DEFAULT_CONFIG)

    print("\n--- Processing Light Curves ---")
    txt_files = glob.glob(os.path.join(input_dir, "*.txt"))
    if not txt_files:
        print("No .txt files found to process in {}".format(input_dir))
        return

    names = [os.path.basename(f) for f in txt_files]
    if not any("_cont" in n for n in names):
        print("WARNING: no '*_cont*' file found - JAVELIN needs a continuum light curve.")
    if not any("_line" in n for n in names):
        print("WARNING: no '*_line*' file found - JAVELIN needs a line light curve.")

    for txt_file in txt_files:
        base_name = os.path.basename(txt_file)
        stem = os.path.splitext(base_name)[0]
        dat_file = os.path.join(output_dir, stem + ".dat")
        try:
            n_data, n_bad = convert_light_curve(txt_file, dat_file)
            print("Converted: {} -> {}".format(base_name, os.path.basename(dat_file)))
            if n_data == 0:
                print("  WARNING: {} has no data rows.".format(base_name))
            elif n_bad:
                print("  WARNING: {} has {}/{} rows that are not 3 numeric columns "
                      "(MJD, flux, error).".format(base_name, n_bad, n_data))
        except Exception as e:
            print("Failed to process {}: {}".format(base_name, e))

    print("\nPreparation finished successfully.")


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_preparation.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add preparation.py tests/test_preparation.py
git commit -m "refactor: extract testable functions in preparation, wire paths"
```

---

### Task 6: `chains2hist.py` helper + histlib shim comment + test

**Files:**
- Modify: `chains2hist.py` (extract `chain_number`, use it in `main`)
- Modify: `histlib.py:22-25` (shim comment wording)
- Create: `tests/test_chains2hist.py`

**Interfaces:**
- Produces: `chains2hist.chain_number(filename, fallback_index) -> str`.

- [ ] **Step 1: Write the failing test `tests/test_chains2hist.py`**

```python
# -*- coding: utf-8 -*-
import chains2hist


def test_chain_number_uses_last_integer():
    assert chains2hist.chain_number('javChain_7.jav', 0) == '7'
    assert chains2hist.chain_number('run2_javChain_13.jav', 0) == '13'


def test_chain_number_falls_back_to_index_plus_one():
    assert chains2hist.chain_number('nochain.jav', 4) == '5'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_chains2hist.py -q`
Expected: FAIL with `AttributeError: 'module' object has no attribute 'chain_number'`.

- [ ] **Step 3: Extract the helper in `chains2hist.py`**

Add above `main()`:
```python
def chain_number(filename, fallback_index):
    """Derive the chain number from the last integer in the filename; fall back
    to str(fallback_index + 1) when the name has no digits."""
    numbers = re.findall(r'\d+', filename)
    return numbers[-1] if numbers else str(fallback_index + 1)
```
In `main()`, replace the inline derivation (`chains2hist.py:74-75`):
```python
            file_num = chain_number(filename, i)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_chains2hist.py -q`
Expected: PASS.

- [ ] **Step 5: Unify the histlib shim comment**

In `histlib.py:22-25`, make the wording match the policy:
```python
try:
    import ConfigParser as configparser  # Python 2 (target runtime)
except ImportError:
    import configparser  # Python 3 fallback (insurance, not a supported target)
```

- [ ] **Step 6: Run full suite**

Run: `python -m pytest tests/ -q`
Expected: PASS (all test files).

- [ ] **Step 7: Commit**

```bash
git add chains2hist.py histlib.py tests/test_chains2hist.py
git commit -m "refactor: extract chain_number helper, unify shim comments"
```

---

### Task 7: Wire `utilities/` scripts to `paths`

These are dev utilities (run as scripts, not imported), so no unit tests — verified by running them.

**Files:**
- Modify: `utilities/lc_gen.py` (output paths → `paths.LIGHT_CURVES`)
- Modify: `utilities/lc_plot.py` (`data_dir` → `paths.LIGHT_CURVES`)

**Interfaces:**
- Consumes: `paths.LIGHT_CURVES`.

- [ ] **Step 1: Add path bootstrap + import in both scripts**

At the top of `utilities/lc_gen.py` and `utilities/lc_plot.py`, after the stdlib imports:
```python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
```

- [ ] **Step 2: Replace hardcoded `../../light_curves` literals**

In `utilities/lc_gen.py` replace `../../light_curves/simulated_cont.txt` / `..._line.txt`:
```python
    cont_file = os.path.join(paths.LIGHT_CURVES, "simulated_cont.txt")
    line_file = os.path.join(paths.LIGHT_CURVES, "simulated_line.txt")
```
In `utilities/lc_plot.py` replace `data_dir = "../../light_curves"`:
```python
    data_dir = paths.LIGHT_CURVES
```

- [ ] **Step 3: Smoke-run the generator**

Run: `cd utilities && python lc_gen.py && cd ..`
Expected: prints success; `simulated_cont.txt` and `simulated_line.txt` appear in `paths.LIGHT_CURVES` (the object's `light_curves/`, created if `preparation.py` ran, else the script's own mkdir).

- [ ] **Step 4: Commit**

```bash
git add utilities/lc_gen.py utilities/lc_plot.py
git commit -m "refactor: route utilities scripts through paths module"
```

---

### Task 8: Full-pipeline verification (gate, no new code)

**Files:** none (verification only).

- [ ] **Step 1: Run the whole test suite under the dev interpreter**

Run: `python -m pytest tests/ -q`
Expected: PASS — `test_histlib`, `test_paths`, `test_run_javelin`, `test_preparation`, `test_chains2hist`.

- [ ] **Step 2: Confirm CWD-independence of preparation**

Run from a directory other than the repo root:
```bash
cd /tmp && python /path/to/scripts/preparation.py && cd -
```
Expected: creates `jav_data`/`results`/`light_curves` next to the object dir (anchored on `paths`), not under `/tmp`.

- [ ] **Step 3: Synthetic smoke (behavioral no-regression)**

`utilities/lc_gen.py` → `preparation.py` → (if JAVELIN present) `run_javelin.py` → `chains2hist.py`. Confirm the exported histogram still marks the injected 3-day lag (`lag_peak ≈ 3`). If JAVELIN is unavailable in the dev env, validate `lc_gen`/`preparation`/`chains2hist` and stub the JAVELIN stage with a prepared `.jav`.

- [ ] **Step 4: Docs sanity grep**

Run: `grep -rn -e 'run-javelin' -e 'hist-tuner' -e 'utilites' . --include='*.md'`
Expected: no matches.

- [ ] **Step 5: Final commit if any doc tweaks were needed**

```bash
git add -A
git commit -m "docs: finalize cleanup verification notes"
```

---

## Self-Review

**Spec coverage:**
- §1 Git hygiene → Task 1. ✓
- §2 Dependency manifest → Task 1. ✓
- §3 Renames + docs → Task 2. ✓
- §4 `paths.py` decoupling → Task 3 (module) + Tasks 4/5/7 (consumers). ✓
- §5 Shim policy → Task 4 (run_javelin) + Task 6 (histlib). ✓
- §6 Tests → Tasks 3–6 (test_paths/test_run_javelin/test_preparation/test_chains2hist). Each test file is self-contained (bootstrap + `_run_all()`); no `conftest.py` because the image lacks pytest — see Testing Protocol. ✓
- Verification plan → Task 8. ✓

**Notes:**
- Two behavior-preserving refactors are load-bearing for testability and were made explicit: moving the stdout hijack into `main()` (Task 4) and extracting functions from the flat `preparation.py` (Task 5). Both keep runtime behavior identical.
- No `scripts/` subdir is ever created (global constraint honored).
- Deferred, tracked separately (not in this plan): adding `ctx_*` MCP allow-rules to `settings.json` — harness config, not repo code.
