#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import math


def generate_light_curves():
    # Time settings (MJD for early March 2030)
    start_mjd = 62560
    days = 7

    # Continuum and line settings (magnitudes)
    cont_base = 17.2
    line_base = 16.6  # Line is brighter (lower value)

    # Flare (peak) settings
    flare_amplitude = 0.7  # How many mag brighter it will get
    cont_peak_mjd = 62561.9
    lag_days = 3.0
    line_peak_mjd = cont_peak_mjd + lag_days
    flare_width = 0.4  # Flare width in days

    # Lists to store data
    cont_data = []
    line_data = []
    cont_file = "../../light_curves/simulated_cont.txt"
    line_file = "../../light_curves/simulated_line.txt"

    # Generate epochs: evening (0.83) and morning of the next day (0.17)
    for day in range(days):
        epochs = [start_mjd + day + 0.83333, start_mjd + day + 1.16667]

        for t in epochs:
            # Generate random error (0.01 - 0.03)
            cont_err = round(random.uniform(0.01, 0.03), 3)
            line_err = round(random.uniform(0.01, 0.03), 3)

            # Mathematical flare model (Gaussian). Minus sign because brighter = lower mag
            cont_flare = flare_amplitude * math.exp(-((t - cont_peak_mjd) ** 2) / (2 * flare_width ** 2))
            line_flare = flare_amplitude * math.exp(-((t - line_peak_mjd) ** 2) / (2 * flare_width ** 2))

            # True value = Base - Flare
            cont_true = cont_base - cont_flare
            line_true = line_base - line_flare

            # Add Gaussian noise within the generated error limits
            cont_obs = cont_true + random.gauss(0, cont_err)
            line_obs = line_true + random.gauss(0, line_err)

            cont_data.append((t, round(cont_obs, 3), cont_err))
            line_data.append((t, round(line_obs, 3), line_err))

    # Write to files
    with open(cont_file, "w") as fc, open(line_file, "w") as fl:
        fc.write("# Simulated light curve (Continuum)\n")
        fc.write("# MJD          Mag       Error\n")
        for pt in cont_data:
            fc.write("{:.5f}    {:.3f}    {:.3f}\n".format(pt[0], pt[1], pt[2]))

        fl.write("# Simulated light curve (Emission line)\n")
        fl.write("# MJD          Mag       Error\n")
        for pt in line_data:
            fl.write("{:.5f}    {:.3f}    {:.3f}\n".format(pt[0], pt[1], pt[2]))


if __name__ == "__main__":
    # Fix the seed for reproducibility (so the same numbers are generated every time)
    random.seed(42)
    generate_light_curves()
    print("Files simulated_cont.txt and simulated_line.txt successfully created.")