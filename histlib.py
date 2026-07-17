# -*- coding: utf-8 -*-
"""
===============================================================================
JAVELIN Batch - Shared Histogram Library
===============================================================================
Author: R. Uklein
Environment: Python 2.7 (legacy, targets JAVELIN v0.33)

Single source of truth for the `hist.ini` schema and the lag-histogram
rendering. Both the GUI tuner (`hist_tuner.py`) and the batch renderer
(`chains2hist.py`) import from here so that the interactive preview and the
exported PNGs are guaranteed identical.

IMPORTANT: this module must stay Python 2.7 compatible and must NOT import
Tkinter at module level, so that `chains2hist.py` can run headless (no X
display). Matplotlib is only touched through the `ax` passed by the caller.
===============================================================================
"""

import re

try:
    import ConfigParser as configparser  # Python 2 (target runtime)
except ImportError:
    import configparser  # Python 3 fallback (insurance, not a supported target)


# ==========================================
# CANONICAL hist.ini SCHEMA
# ==========================================
# {Section: [(key, type), ...]}. This is the one place that defines the layout
# of hist.ini. The histogram column lives in [Plot] (key 'column'); axis limits
# and 'lag_peak' are floats so fractional lags work.
INI_SCHEMA = {
    'Path': [
        ('data_dir', 'str'),
        ('file_pattern', 'str'),
        ('output_dir', 'str'),
    ],
    'Plot': [
        ('column', 'int'),
        ('bins', 'int'),
        ('x_min', 'float'),
        ('x_max', 'float'),
        ('y_min', 'float'),
        ('y_max', 'float'),
        ('dpi', 'int'),
    ],
    'Annotations': [
        ('agn_name', 'str'),
        ('comment', 'str'),
        ('x_label', 'str'),
        ('y_label', 'str'),
        ('lag_peak', 'float'),
        ('lag_label', 'str'),
        ('lab_font_size', 'int'),
        ('title_font_size', 'int'),
    ],
    'Style': [
        ('yaxis_right', 'bool'),
        ('hist_color', 'str'),
        ('line_color', 'str'),
    ],
}

# Default colors. Persisted to hist.ini by the GUI and read back by the batch.
DEFAULT_HIST_COLOR = '#601fb4'
DEFAULT_LINE_COLOR = '#ff0000'


def natural_sort_key(s):
    """Sort key so files order naturally (10 after 9, not after 1)."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]


def _coerce(value, ktype):
    """Convert a raw string config value to the type declared in INI_SCHEMA."""
    if ktype == 'int':
        return int(value)
    if ktype == 'float':
        return float(value)
    if ktype == 'bool':
        # configparser cannot getboolean on an arbitrary string; normalize here.
        return str(value).strip().lower() in ('1', 'true', 'yes', 'on')
    return str(value)


def load_hist_config(path):
    """
    Read hist.ini into a flat, properly typed dict following INI_SCHEMA.

    Backward compatibility:
        - The histogram column is read from [Plot] column; if absent, falls back
          to the legacy [Data] column_number, then to 3.
        - hist_color / line_color fall back to module defaults when missing.

    Parameters
    ----------
    path : str
        Path to the hist.ini file.

    Returns
    -------
    dict
        Mapping of key -> typed value for every key in INI_SCHEMA.
    """
    config = configparser.SafeConfigParser()
    config.read(path)

    cfg = {}
    for section, keys in INI_SCHEMA.items():
        for key, ktype in keys:
            raw = None
            if config.has_section(section) and config.has_option(section, key):
                raw = config.get(section, key)

            if raw is None or raw == '':
                # Per-key fallbacks for missing/empty values.
                if key == 'column':
                    if (config.has_section('Data')
                            and config.has_option('Data', 'column_number')):
                        raw = config.get('Data', 'column_number')
                    else:
                        raw = '3'
                elif key == 'hist_color':
                    raw = DEFAULT_HIST_COLOR
                elif key == 'line_color':
                    raw = DEFAULT_LINE_COLOR
                elif ktype == 'str':
                    # An empty string is a legitimate value (e.g. comment).
                    cfg[key] = ''
                    continue
                elif ktype == 'bool':
                    cfg[key] = False
                    continue
                else:
                    # Numeric keys (bins, dpi, axis limits, ...) have no safe
                    # default: a silent 0 yields blank/degenerate plots. Fail
                    # loudly with the offending key, like config.getint used to.
                    raise ValueError(
                        "hist.ini: missing or empty required value '%s' in [%s]"
                        % (key, section))

            cfg[key] = _coerce(raw, ktype)

    return cfg


def plot_histogram(ax, column_data, cfg):
    """
    Render a single lag histogram onto a Matplotlib axes from a config dict.

    Shared by the GUI preview and the batch exporter to keep them identical.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes (caller owns figure creation / saving).
    column_data : array-like
        1-D array of lag samples (already extracted from the chain).
    cfg : dict
        Typed config as produced by `load_hist_config` (or assembled by the GUI
        with the same keys: bins, x_min/x_max/y_min/y_max, hist_color,
        line_color, lag_peak, lag_label, x_label, y_label, lab_font_size,
        agn_name, comment, title_font_size, yaxis_right).
    """
    ax.hist(column_data, bins=cfg['bins'],
            color=cfg['hist_color'], edgecolor='black')

    ax.set_xlim(cfg['x_min'], cfg['x_max'])
    ax.set_ylim(cfg['y_min'], cfg['y_max'])

    ax.axvline(x=cfg['lag_peak'], color=cfg['line_color'], linestyle='--')

    ax.text(cfg['lag_peak'] + 0.1, cfg['y_max'] * 0.9, cfg['lag_label'],
            fontsize=cfg['lab_font_size'], horizontalalignment='left')

    ax.set_xlabel(cfg['x_label'], fontsize=cfg['lab_font_size'])
    ax.set_ylabel(cfg['y_label'], fontsize=cfg['lab_font_size'])

    full_title = "JAVELIN analysis for %s\n%s" % (cfg['agn_name'], cfg['comment'])
    ax.set_title(full_title, fontsize=cfg['title_font_size'])

    if cfg['yaxis_right']:
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
