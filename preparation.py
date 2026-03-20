#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
===============================================================================
JAVELIN Data Preparation Script
===============================================================================
Author: R. Uklein
Date: 2026
Environment: Python 2.7 (Ubuntu 18.04)

Description:
    1. Creates required directory structure for data, results, and backups.
    2. Generates a default JAVELIN configuration file (start1.cfg).
    3. Cleans raw .txt light curves and converts them to .dat format.

Directory Structure Created:
    - ../jav_data / _sessions
    - ../results / _sessions
    - ../light_curves / _backup
===============================================================================
"""

import os
import glob
import io

# ==========================================
# CONFIGURATION
# ==========================================
input_dir = "../light_curves"
output_dir = "../jav_data"

# List of all directories to ensure exist
dirs_to_ensure = [
    "../jav_data",
    "../jav_data/_sessions",
    "../results",
    "../results/_sessions",
    "../light_curves",
    "../light_curves/_versions"
]

# Content for the default configuration file
config_path = os.path.join(input_dir, "start1.cfg")
config_content = u"""[paths]
cont_pattern = ../jav_data/*_cont*.dat
line_pattern = ../jav_data/*_line*.dat
chains_path = ../jav_data/chains_run1/
log_path = logs/run1.log

[mcmc]
n_walkers = 100
n_burn = 500
n_chain = 500
lag_limit_min = 0
lag_limit_max = 10
n_iter = 1
"""

# ==========================================
# 1. DIRECTORY SETUP
# ==========================================
print("--- Initializing Directory Structure ---")
for d in dirs_to_ensure:
    if not os.path.exists(d):
        try:
            os.makedirs(d)
            print("Created: {}".format(d))
        except Exception as e:
            print("Error creating {}: {}".format(d, e))
    else:
        print("Exists:  {}".format(d))

# ==========================================
# 2. CREATE DEFAULT CONFIG FILE
# ==========================================
print("\n--- Checking Configuration Files ---")
if not os.path.exists(config_path):
    try:
        with io.open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)
        print("Created default config: {}".format(config_path))
    except Exception as e:
        print("Error creating config: {}".format(e))
else:
    print("Config already exists: {}".format(config_path))

# ==========================================
# 3. DATA PROCESSING (.txt to .dat)
# ==========================================
print("\n--- Processing Light Curves ---")

search_pattern = os.path.join(input_dir, "*.txt")
txt_files = glob.glob(search_pattern)

if not txt_files:
    print("No .txt files found to process in {}".format(input_dir))
else:
    for txt_file in txt_files:
        base_name = os.path.basename(txt_file)
        stem = os.path.splitext(base_name)[0]
        dat_file = os.path.join(output_dir, stem + ".dat")

        try:
            # Using io.open for Python 2/3 encoding and newline compatibility
            with io.open(txt_file, "r", encoding="utf-8") as f_in, \
                    io.open(dat_file, "w", encoding="utf-8", newline=u"\n") as f_out:

                for line in f_in:
                    line = line.strip()

                    # Skip empty lines or header comments
                    if not line or line.startswith(u"#"):
                        continue

                    # Write clean data line
                    f_out.write(line + u"\n")

            print("Converted: {} -> {}".format(base_name, os.path.basename(dat_file)))

        except Exception as e:
            print("Failed to process {}: {}".format(base_name, e))

print("\nPreparation finished successfully.")