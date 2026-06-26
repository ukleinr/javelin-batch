# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A batch-processing toolkit around **JAVELIN v0.33** (https://github.com/nye17/javelin) for
estimating time lags between AGN photometric light curves (continuum vs. emission line). It
prepares raw photometry, runs MCMC modeling in bulk, and renders lag histograms.

## Critical constraints

- **Python 2.7 only.** This is legacy code targeting JAVELIN v0.33 on Ubuntu 18.04. Run every
  script with `python2`, never `python3`. Use Python 2 idioms: `ConfigParser`/`Tkinter` (capitalized
  module names), `print` semantics, `.format()` instead of f-strings, `io.open` for encoding control.
  This overrides the global instruction to target Python 3.8+ / Windows.
- **Hardcoded relative paths.** The four pipeline scripts assume the current working directory is the
  object's `scripts/` folder and reference `../jav_data`, `../light_curves`, `../results` directly.
  They must be run from inside `scripts/`. The `utilites/` scripts instead use `../../light_curves`
  (i.e. they expect to run from `scripts/utilites/`).
- GUI scripts (`hist-tuner.py`, `lc_plot.py`) need an X display and Tkinter; the intended host is a
  Docker container (Ubuntu 18.04) with an X server (VcXsrv/Xming) on Windows. See `README.md` for the
  full Docker invocation.

## Pipeline (run in order, from `scripts/`)

1. `python2 preparation.py` — creates the directory tree, writes a default `start1.cfg` into
   `../light_curves/`, and converts raw `../light_curves/*.txt` (3 cols: MJD, flux/mag, error;
   `#` comments stripped) into `../jav_data/*.dat`.
2. `python2 run-javelin.py` — finds **all** `../light_curves/*.cfg`, runs each sequentially. Per cfg:
   fits `Cont_Model`, then loops `n_iter` times producing `javChain_<n>.jav` MCMC chains in `chains_path`.
3. `python2 hist-tuner.py` — Tkinter GUI to interactively tune one histogram; saves settings to `hist.ini`.
4. `python2 chains2hist.py` — reads `hist.ini`, naturally sorts all `*.jav`, writes one PNG per chain to `output_dir`.

There is no build step, test suite, linter config, or dependency manifest in this repo. Dependencies
(`javelin`, `numpy`, `matplotlib`, Tkinter) are expected to be preinstalled in the runtime image.

## Architecture notes

- **`run-javelin.py` logging.** It hijacks `sys.stdout`/`sys.stderr` via `StreamToLogger` so JAVELIN's
  internal prints land in per-config log files, while a colored console handler + a manual progress bar
  write to the saved `original_stdout`/`original_stderr` only. A `FileHandler` is added/removed per cfg
  so each config logs to its own `log_path`. `sys.stdout`/`stderr` are restored in a `finally` block —
  preserve that when editing, or a crash leaves the terminal mute.
- **`javelin` is imported lazily** inside `run_javelin()` (not at module top) so the rest of the script
  loads even without JAVELIN installed.
- **MCMC contract:** `Cont_Model.do_mcmc()` → `cmod.hpd` feeds `Pmap_Model.do_mcmc(conthpd=..., laglimit=[[min,max]])`.
  The lag column in each `.jav` chain is column 3 (1-based).

## Shared rendering & config (`histlib.py`)

`histlib.py` is the single source of truth for both the `hist.ini` schema and the lag-histogram
rendering. `hist-tuner.py` (GUI preview) and `chains2hist.py` (batch export) both import it, so the
preview is guaranteed to match the exported PNGs.

- `INI_SCHEMA` — canonical layout. The column lives in `[Plot] column`; axis limits and `lag_peak`
  are floats. `[Style]` holds `yaxis_right`, `hist_color`, `line_color`.
- `load_hist_config(path)` — returns a flat, typed dict. Backward compatible: falls back to the legacy
  `[Data] column_number` for the column, and to `DEFAULT_HIST_COLOR`/`DEFAULT_LINE_COLOR` for missing colors.
- `plot_histogram(ax, column_data, cfg)` — the shared renderer; the caller owns figure creation/saving.
- `histlib` must stay Python 2.7 compatible and must **not** import Tkinter at module level, so
  `chains2hist.py` runs headless (it sets the `Agg` matplotlib backend). Tkinter lives only in `hist-tuner.py`.

The GUI now persists `hist_color`/`line_color` to `[Style]`, and the batch reads them from there.

## Conventions

- Comments, docstrings, identifiers, commits: English. Discussion with the maintainer: Russian.
- Light-curve `.txt`/`.dat` files: continuum files carry a `_cont` suffix, line files `_line`; the glob
  patterns in cfg/ini depend on these.
