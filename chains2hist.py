# -*- coding: utf-8 -*-
import os
import glob
import re
import ConfigParser
import numpy as np
import matplotlib.pyplot as plt


# Function for natural sorting of files (so 10 comes after 9, not after 1)
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


def main():
    # 1. Read configuration from hist.ini
    config = ConfigParser.SafeConfigParser()
    config.read('hist.ini')

    # Paths
    data_dir = config.get('Path', 'data_dir')
    file_pattern = config.get('Path', 'file_pattern')
    output_dir = config.get('Path', 'output_dir')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Data (convert 1-based column number to 0-based index for Python)
    col_index = config.getint('Data', 'column_number') - 1

    # Plot parameters
    bins = config.getint('Plot', 'bins')
    x_min = config.getint('Plot', 'x_min')
    x_max = config.getint('Plot', 'x_max')
    y_min = config.getint('Plot', 'y_min')
    y_max = config.getint('Plot', 'y_max')
    dpi = config.getint('Plot', 'dpi')

    # Annotations and text
    agn_name = config.get('Annotations', 'agn_name')
    comment = config.get('Annotations', 'comment')
    x_label = config.get('Annotations', 'x_label')
    y_label = config.get('Annotations', 'y_label')
    lag_peak = config.getint('Annotations', 'lag_peak')
    lag_label = config.get('Annotations', 'lag_label')
    lab_font_size = config.getint('Annotations', 'lab_font_size')
    title_font_size = config.getint('Annotations', 'title_font_size')

    yaxis_right = config.getboolean('Style', 'yaxis_right')

    # 2. Find and sort files
    search_path = os.path.join(data_dir, file_pattern)
    files = glob.glob(search_path)
    files = sorted(files, key=natural_sort_key)  # Equivalent to seq=0:49 in MATLAB

    if not files:
        print("No files found matching pattern: %s" % search_path)
        return

    print("Found files to process: %d" % len(files))

    # 3. Prepare figure and axes (Equivalent to h1 = figure in MATLAB)
    fig, ax = plt.subplots()

    # 4. Main loop over files (Equivalent to for i=seq)
    for i, filepath in enumerate(files):
        filename = os.path.basename(filepath)
        print("Processing: %s" % filename)

        try:
            # Read data (equivalent to importdata in MATLAB)
            data = np.loadtxt(filepath)

            # Extract the required column (lag)
            column_data = data[:, col_index]

            # Clear axes for the new frame
            ax.cla()

            # Plot histogram
            ax.hist(column_data, bins=bins, color='#601fb4', edgecolor='black')

            # Fix axes limits
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)

            # Draw dashed red line
            ax.axvline(x=lag_peak, color='red', linestyle='--')

            # Add '1 month' text (equivalent to text(...))
            ax.text(lag_peak + 0.1, y_max * 0.9, lag_label,
                    fontsize=lab_font_size, horizontalalignment='left')

            # Axis labels
            ax.set_xlabel(x_label, fontsize=lab_font_size)
            ax.set_ylabel(y_label, fontsize=lab_font_size)

            # Two-line title
            full_title = "JAVELIN analysis for %s\n%s" % (agn_name, comment)
            ax.set_title(full_title, fontsize=title_font_size)

            # Move Y-axis to the right (equivalent to ax.YAxisLocation = 'right')
            if yaxis_right:
                ax.yaxis.tick_right()
                ax.yaxis.set_label_position("right")

            # 5. Save image
            numbers = re.findall(r'\d+', filename)
            file_num = numbers[-2] if len(numbers) >= 2 else str(i+1)

            out_filename = "jav_%s_lag_chain%s.png" % (agn_name, file_num)
            out_filepath = os.path.join(output_dir, out_filename)

            fig.savefig(out_filepath, dpi=dpi, bbox_inches='tight')

        except Exception as e:
            print(" -> Error reading %s: %s" % (filename, str(e)))

    # Close figure to free memory
    plt.close(fig)
    print("All images successfully saved to: %s" % os.path.abspath(output_dir))


if __name__ == '__main__':
    main()