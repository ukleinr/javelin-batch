# -*- coding: utf-8 -*-
"""
===============================================================================
JAVELIN Batch - Histogram Exporter
===============================================================================
Author: R. Uklein
Environment: Python 2.7 (legacy, targets JAVELIN v0.33)

Reads the shared hist.ini config, finds all chain files, and exports one lag
histogram PNG per chain. Rendering and config parsing are delegated to
`histlib` so the output matches the GUI preview exactly. Runs headless (no
Tkinter / X display required).
===============================================================================
"""

import os
import glob
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')  # headless backend: no X display needed for batch export
import matplotlib.pyplot as plt

import histlib


def main():
    # 1. Load the shared, typed configuration
    cfg = histlib.load_hist_config('hist.ini')

    data_dir = cfg['data_dir']
    file_pattern = cfg['file_pattern']
    output_dir = cfg['output_dir']

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Convert 1-based column number to 0-based index for numpy
    col_index = cfg['column'] - 1
    dpi = cfg['dpi']
    agn_name = cfg['agn_name']

    # 2. Find and naturally sort files
    search_path = os.path.join(data_dir, file_pattern)
    files = glob.glob(search_path)
    files = sorted(files, key=histlib.natural_sort_key)

    if not files:
        print("No files found matching pattern: %s" % search_path)
        return

    print("Found files to process: %d" % len(files))

    # 3. Prepare a single reusable figure/axes
    fig, ax = plt.subplots()

    # 4. Main loop over files
    for i, filepath in enumerate(files):
        filename = os.path.basename(filepath)
        print("Processing: %s" % filename)

        try:
            data = np.loadtxt(filepath)
            column_data = data[:, col_index]

            # Clear axes and render via the shared plotter
            ax.cla()
            histlib.plot_histogram(ax, column_data, cfg)

            # Derive the chain number from the filename (last number), fall back
            # to the loop index. e.g. "javChain_7.jav" -> "7".
            numbers = re.findall(r'\d+', filename)
            file_num = numbers[-1] if numbers else str(i + 1)

            out_filename = "jav_%s_lag_chain%s.png" % (agn_name, file_num)
            out_filepath = os.path.join(output_dir, out_filename)

            fig.savefig(out_filepath, dpi=dpi, bbox_inches='tight')

        except Exception as e:
            print(" -> Error reading %s: %s" % (filename, str(e)))

    plt.close(fig)
    print("All images successfully saved to: %s" % os.path.abspath(output_dir))


if __name__ == '__main__':
    main()
