#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
===============================================================================
JAVELIN Data Preparation Script
===============================================================================
Author: R. Uklein
Environment: Python 2.7 (Ubuntu 18.04)

Description:
    1. Creates required directory structure for data, results, and backups.
    2. Generates a default JAVELIN configuration file (start1.cfg).
    3. Cleans raw .txt light curves and converts them to .dat format.
===============================================================================
"""

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
