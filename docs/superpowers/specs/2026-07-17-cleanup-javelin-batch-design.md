# Cleanup javelin-batch — design spec

Date: 2026-07-17 · Branch: `refactor/optimize-legacy-pipeline` · Status: approved design, pending implementation plan

## Context

`javelin-batch` is a small (8 `.py`, ~1450 LoC) set of Python 2.7 batch/wrapper scripts around JAVELIN v0.33 for AGN reverberation-mapping time-lag estimation. It is not a library and does not vendor JAVELIN — `run-javelin.py` lazily imports an externally installed `javelin`. The code works but carries legacy hygiene debt: no `.gitignore` (a stray `__pycache__/histlib.cpython-38.pyc` sits in the tree), no dependency manifest, hyphenated non-importable filenames, a misspelled `utilites/` directory, CWD-fragile hardcoded relative paths, incidental (undocumented) Py2/3 shims, and test coverage limited to `histlib`. This spec cleans up that debt without changing pipeline behavior, output contracts, or the Python 2.7 target. pyPETAL integration is explicitly a separate project in a separate repo and is out of scope here.

## Constraints (hard)

- **Strictly Python 2.7.** The whole repo targets JAVELIN v0.33 on Ubuntu 18.04. Existing Py2/3 shims stay as defensive insurance but 2.7 is the only supported runtime. This overrides the global Py3.8+ default.
- **The repo *is* the object's `scripts/` folder.** It is deployed as `object1/scripts/` (`docker run ... -w /workspace/object1/scripts`). Sibling data dirs are `../jav_data`, `../light_curves`, `../results`; `utilities/` scripts run one level deeper and use `../../`. Therefore **do not create a `scripts/` subdirectory** — it would double-nest and break every relative path. The README's `scripts/` in its tree diagrams refers to this checkout, not a subfolder; docs are correct as-is on that point.
- **Do not change data/output contracts:** the `.cfg` schema, `hist.ini` schema, `.dat`/`.jav` formats, the lag-column-3 convention, and the MCMC contract (`Cont_Model.hpd` → `Pmap_Model.do_mcmc(conthpd=..., laglimit=[[min,max]])`) all stay untouched.

## Scope — work items

### 1. Git hygiene

Add `.gitignore` covering `__pycache__/`, `*.pyc`, generated data/results (`*.dat`, `*.jav`, `*.png`, `results/`, `jav_data/`), and local editor/OS cruft. Remove the tracked-adjacent stray `__pycache__/histlib.cpython-38.pyc` from the working tree.

### 2. Dependency manifest

Add `requirements.txt` pinned for Python 2.7: `numpy==1.16.6` and `matplotlib==2.2.5` (the last releases supporting 2.7). Tkinter is stdlib (documented as an OS package `python-tk`). `javelin` is external and noted as a comment (`# javelin @ git+https://github.com/nye17/javelin.git@0.33`), not pip-resolved. No `setup.py`/`pyproject.toml` — this is a script set, not a distributable package. Pins **verified against `ub18-jav:latest` (2026-07-17): Python 2.7.17, numpy 1.16.6, matplotlib 2.2.5** — they match exactly.

### 3. Renames (breaks run commands → docs updated in lockstep)

- `utilites/` → `utilities/`
- `run-javelin.py` → `run_javelin.py`
- `hist-tuner.py` → `hist_tuner.py`

Rationale: hyphens make files non-importable, blocking tests. `histlib.py`, `chains2hist.py`, `preparation.py` are already valid identifiers and are left as-is. Update every `python2 run-javelin.py` / `python2 hist-tuner.py` invocation and file listing in `README.md`, `readme-ru.md`, `QUICKSTART.md`, and `CLAUDE.md`.

### 4. Path decoupling (`paths.py`)

New shared module `paths.py` (repo root = `scripts/`) that resolves the object's data directories from **its own `__file__` location** rather than the process CWD: `OBJECT_DIR = dirname(dirname(abspath(paths.__file__)))`, then `JAV_DATA`, `LIGHT_CURVES`, `RESULTS` as `os.path.join(OBJECT_DIR, ...)`. Consumers (`preparation.py`, `run_javelin.py`'s hardcoded `config_dir`, `utilities/lc_gen.py`, `utilities/lc_plot.py`) import these constants instead of literal `../…` / `../../…` strings, which also removes the `../` vs `../../` divergence and makes scripts CWD-independent while resolving to the identical locations in normal use.

**Boundary (important):** this covers only *script-hardcoded scaffolding paths*. The glob patterns *inside user `.cfg` files* (`cont_pattern = ../jav_data/*_cont*.dat`, `chains_path`, `log_path`) are user-owned data and stay CWD-relative and untouched — `paths.py` does not rewrite them. In normal operation (run from `scripts/`) the `__file__` anchor equals the CWD, so cfg-relative globs and anchored paths resolve to the same tree. `utilities/` scripts add the parent (`scripts/`) to `sys.path` to import `paths`.

### 5. Py2/3 shim policy

Keep the shims (`ConfigParser`/`configparser`, `NavigationToolbar2Tk`/`NavigationToolbar2TkAgg`) as insurance but make them consistent and documented: prefer the Python-2 name first everywhere (target runtime), and add a one-line comment marking them "insurance, not a supported target." Currently `run-javelin.py` tries `configparser` first while `histlib.py` tries `ConfigParser` first — unify to ConfigParser-first.

### 6. Tests

Extend coverage beyond `histlib` (all tests must pass under Python 2.7; keep incidental 3.8 compatibility already present):

- `preparation.py` — 3-column row validation / comment stripping / `.dat` conversion.
- `run_javelin.py` — `load_config` parsing and `validate_settings` (incl. `lag_limit_min >= lag_limit_max` rejection).
- `chains2hist.py` — natural sort ordering and lag-column extraction.
- `paths.py` — anchored resolution is CWD-independent and equals the legacy `../…` targets when run from `scripts/`.

Replace the `sys.path` hack in `tests/test_histlib.py` with a `conftest.py` that puts the repo root on `sys.path`. Keep the existing manual `_run_all()` fallback so tests run without pytest on the Py2.7 image.

## Out of scope

- Creating a `scripts/` subdirectory (would break paths — see constraints).
- Any change to the MCMC flow, `.jav`/`hist.ini`/`.cfg`/`.dat` formats, or the lag-column convention.
- Porting anything to Python 3; pyPETAL integration (separate repo/project).
- Turning the repo into an installable package (`__init__.py` at root, `setup.py`).

## File-by-file impact

- **New:** `.gitignore`, `requirements.txt`, `paths.py`, `tests/conftest.py`, `tests/test_preparation.py`, `tests/test_run_javelin.py`, `tests/test_chains2hist.py`, `tests/test_paths.py`, this spec.
- **Renamed:** `utilites/` → `utilities/`, `run-javelin.py` → `run_javelin.py`, `hist-tuner.py` → `hist_tuner.py`.
- **Edited:** `preparation.py`, `run_javelin.py`, `utilities/lc_gen.py`, `utilities/lc_plot.py` (import from `paths`); `histlib.py` + `run_javelin.py` (shim comment/order); `README.md`, `readme-ru.md`, `QUICKSTART.md`, `CLAUDE.md` (new filenames, `utilities/` spelling).
- **Removed:** stray `__pycache__/histlib.cpython-38.pyc`.

## Verification (end-to-end)

1. **Tests:** run the suite under Python 2.7 (`python2 -m pytest tests/` or each file's `_run_all()`); all pass. Also confirm they still pass under 3.8 (dev machine).
2. **Path anchor:** run `preparation.py` from a *different* CWD than `scripts/` and confirm it creates the same `jav_data`/`light_curves`/`results` tree next to the object dir (CWD-independence works).
3. **Synthetic smoke:** `utilities/lc_gen.py` → `preparation.py` → (JAVELIN present) `run_javelin.py` → `chains2hist.py`; the injected 3-day lag (from `lc_gen.py`) still surfaces as `lag_peak ≈ 3` in the exported histogram — proving no behavioral regression. If JAVELIN is unavailable in the dev env, validate stages 1, 2, 4 and stub stage 3 with a prepared `.jav`.
4. **Docs:** grep the docs for the old `run-javelin.py` / `hist-tuner.py` / `utilites` strings — none remain.

## Notes / deferred

- Separately from this repo cleanup (harness config, not code): add allow-rules for the `ctx_*` context-mode MCP tools to `settings.json` so those permission prompts stop — per the maintainer's earlier request.
