#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import sys
import glob
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths


def mjd_to_datetime(mjd):
    """
    Convert Modified Julian Date (MJD) to a Python datetime object.
    MJD 40587 corresponds to 1970-01-01 00:00:00 UTC.
    """
    return datetime(1970, 1, 1) + timedelta(days=mjd - 40587)


def main():
    # Base directory for data and output plot
    data_dir = paths.LIGHT_CURVES

    # Patterns to find the files (using glob)
    cont_pattern = os.path.join(data_dir, "*_cont*.txt")
    line_pattern = os.path.join(data_dir, "*_line*.txt")

    # Search for files
    cont_files = glob.glob(cont_pattern)
    line_files = glob.glob(line_pattern)

    # Check if files were found
    if not cont_files:
        print("Error: No continuum files found matching pattern: %s" % cont_pattern)
        sys.exit(1)

    if not line_files:
        print("Error: No emission line files found matching pattern: %s" % line_pattern)
        sys.exit(1)

    # If multiple files match, we pick the first one from the list
    cont_file = cont_files[0]
    line_file = line_files[0]

    print("Found continuum file: %s" % cont_file)
    print("Found line file:      %s" % line_file)

    # Load data using numpy (ignores comments automatically)
    try:
        cont_data = np.loadtxt(cont_file)
        line_data = np.loadtxt(line_file)
    except IOError as e:
        print("IOError while reading files:", e)
        sys.exit(1)

    # Extract columns: MJD [0], Mag [1], Error [2]
    # (Checking if arrays are 1D in case file has only one row)
    if cont_data.ndim == 1: cont_data = cont_data.reshape(1, -1)
    if line_data.ndim == 1: line_data = line_data.reshape(1, -1)

    cont_mjd, cont_mag, cont_err = cont_data[:, 0], cont_data[:, 1], cont_data[:, 2]
    line_mjd, line_mag, line_err = line_data[:, 0], line_data[:, 1], line_data[:, 2]

    # Convert MJD to real dates
    cont_dates = [mjd_to_datetime(m) for m in cont_mjd]
    line_dates = [mjd_to_datetime(m) for m in line_mjd]

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot Continuum with error bars
    ax.errorbar(cont_dates, cont_mag, yerr=cont_err, fmt='o-', color='blue',
                label='Continuum', capsize=4, markersize=6, elinewidth=1.5)

    # Plot Emission Line with error bars
    ax.errorbar(line_dates, line_mag, yerr=line_err, fmt='s-', color='red',
                label='Emission Line', capsize=4, markersize=6, elinewidth=1.5)

    # Invert Y-axis because in astronomy lower magnitude = brighter object
    ax.invert_yaxis()

    # Format the X-axis to show real dates (YYYY-MM-DD)
    date_format = mdates.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_formatter(date_format)

    # Auto-rotate the dates so they don't overlap
    fig.autofmt_xdate()

    # Add labels, title, and grid
    ax.set_xlabel('Date (UTC)', fontsize=12)
    ax.set_ylabel('Magnitude (mag)', fontsize=12)
    ax.set_title('Simulated AGN Light Curves', fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.6)

    # Add legend
    ax.legend(loc='best', fontsize=12)

    # Adjust layout to prevent label clipping
    plt.tight_layout()

    # Ensure output directory exists (in case it was deleted during runtime)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Save the resulting plot to the target directory
    output_filename = os.path.join(data_dir, 'light_curves.png')
    plt.savefig(output_filename, dpi=300)

    print("Plot successfully saved to: '%s'" % output_filename)


if __name__ == "__main__":
    main()