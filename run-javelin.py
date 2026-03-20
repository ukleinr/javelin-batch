#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
===============================================================================
JAVELIN Batch Processor
===============================================================================
Author: R. Uklein
Date: 2026
Environment: Python 2.7 (Ubuntu 18.04)

Description:
    This script automates the execution of JAVELIN (Just Another Vehicle for
    Estimating Lags In Nuclei) MCMC models across multiple datasets. It
    searches for all '.cfg' configuration files in the specified directory
    and processes them sequentially.

Key Features:
    - Multi-configuration batch execution.
    - Console stdout/stderr redirection: captures all internal JAVELIN
      print statements and passes them to the logging system.
    - Dynamic Logging: generates a clean, plain-text log file for each
      configuration while maintaining a colored output in the terminal.
    - Custom console progress bar for the MCMC iteration sequence.

Config File Example (*.cfg):
    [paths]
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
===============================================================================
"""

import glob
import time
import os
import sys
import logging

try:
    import configparser
except ImportError:
    import ConfigParser as configparser  # Python 2 compatibility


# ==========================================
# STDOUT/STDERR REDIRECTION CLASS
# ==========================================
class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    This ensures that external library prints are captured in our log files.
    """

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            # Ignore empty lines to avoid log clutter
            if line.strip():
                self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass


# ==========================================
# COLORED FORMATTER FOR PYTHON 2
# ==========================================
class ColoredFormatter(logging.Formatter):
    """
    Python 2 compatible colored formatter for console output.
    """
    COLORS = {
        'DEBUG': '\033[94m',      # Blue
        'INFO': '\033[92m',       # Green
        'WARNING': '\033[93m',    # Yellow
        'ERROR': '\033[91m',      # Red
        'CRITICAL': '\033[95m'    # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        # 1. Get the base string (time + level + text)
        log_message = logging.Formatter.format(self, record)
        # 2. Add color based on the log level
        color = self.COLORS.get(record.levelname, '')
        if color:
            # Use .format() instead of f-strings for Python 2 compatibility
            return "{}{}{}".format(color, log_message, self.RESET)
        return log_message


# ==========================================
# BASE LOGGING SETUP
# ==========================================
# 1. Save the original stdout/stderr before we overwrite them
original_stdout = sys.__stdout__
original_stderr = sys.__stderr__

# 2. Initialize base logger
logger = logging.getLogger('JAVELIN_BATCH')
logger.setLevel(logging.INFO)

# Create two formatters: colored (for console) and standard (for files)
log_format_str = '%(asctime)s [%(levelname)s] %(message)s'
console_formatter = ColoredFormatter(log_format_str)
file_formatter = logging.Formatter(log_format_str)

# Console handler (prints ONLY to the original stdout)
ch = logging.StreamHandler(original_stdout)
ch.setFormatter(console_formatter)  # Console will have colored output!
logger.addHandler(ch)

# 3. Redirect stdout and stderr to the logger
sys.stdout = StreamToLogger(logger, logging.INFO)
sys.stderr = StreamToLogger(logger, logging.ERROR)

filler_length = 48  # '='*filler_length = '==============='

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def print_progress(iteration, total, prefix='', suffix='', length=40, fill='▮'):
    """
    Call in a loop to create a terminal progress bar.
    Writes directly to original_stdout so it doesn't clutter the .log files.
    """
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)

    # We use original_stdout so the progress bar only shows in console
    # Added cyan color (\033[96m) to make the progress bar look distinct
    original_stdout.write('\r\033[96m%s |%s| %s%% %s\033[0m' % (prefix, bar, percent, suffix))
    original_stdout.flush()

    # Print New Line on Complete
    if iteration == total:
        original_stdout.write('\n')


def load_config(config_path):
    """Reads parameters from a .cfg file and returns a dictionary."""
    config = configparser.ConfigParser()
    config.read(config_path)

    settings = {
        'cont_pattern': config.get('paths', 'cont_pattern'),
        'line_pattern': config.get('paths', 'line_pattern'),
        'chains_path':  config.get('paths', 'chains_path'),
        'log_path':     config.get('paths', 'log_path'),
        'n_walkers':    config.getint('mcmc', 'n_walkers'),
        'n_burn':       config.getint('mcmc', 'n_burn'),
        'n_chain':      config.getint('mcmc', 'n_chain'),
        'lag_limit_min': config.getfloat('mcmc', 'lag_limit_min'),
        'lag_limit_max': config.getfloat('mcmc', 'lag_limit_max'),
        'n_iter':       config.getint('mcmc', 'n_iter'),
    }
    return settings


def run_javelin(settings, config_name):
    """Runs JAVELIN MCMC for a single configuration."""
    logger.info("=" * filler_length)
    logger.info("Running config: %s", config_name)
    logger.info("=" * filler_length)

    # --- Find input files ---
    cont_files = sorted(glob.glob(settings['cont_pattern']))
    line_files = sorted(glob.glob(settings['line_pattern']))

    if not cont_files:
        logger.error("No cont files found for pattern: %s", settings['cont_pattern'])
        return None
    if not line_files:
        logger.error("No line files found for pattern: %s", settings['line_pattern'])
        return None

    logger.info("cont file: %s", cont_files[0])
    logger.info("line file: %s", line_files[0])

    # --- MCMC Parameters ---
    n_walkers   = settings['n_walkers']
    n_burn      = settings['n_burn']
    n_chain     = settings['n_chain']
    lag_limit   = [settings['lag_limit_min'], settings['lag_limit_max']]
    n_iter      = settings['n_iter']
    chains_path = settings['chains_path']

    # --- Create chains directory ---
    if not os.path.exists(chains_path):
        os.makedirs(chains_path)
        logger.info("Directory %s created", chains_path)
    else:
        logger.info("Directory %s already exists", chains_path)

    # --- JAVELIN initialization ---
    from javelin.zylc import get_data
    from javelin.lcmodel import Cont_Model, Pmap_Model

    t = time.time()

    # Cont model
    logger.info("Starting Cont_Model MCMC...")
    c = get_data([cont_files[0]])
    cmod = Cont_Model(c)
    # Prints inside do_mcmc() will be caught by StreamToLogger and logged
    cmod.do_mcmc()

    # Pmap model
    logger.info("Starting Pmap_Model initialization...")
    cyb = get_data([cont_files[0], line_files[0]])
    cybmod = Pmap_Model(cyb)

    # --- Iteration Loop with Progress Bar ---
    logger.info("Starting iteration sequence (%d iterations)...", n_iter)

    # Initial call to print 0% progress to console
    print_progress(0, n_iter, prefix='Progress:', suffix='Complete\n', length=40)

    for i in range(n_iter):
        chain_file = os.path.join(chains_path, "javChain_" + str(i + 1) + ".jav")

        cybmod.do_mcmc(
            conthpd=cmod.hpd,
            fchain=chain_file,
            nwalkers=n_walkers,
            nburn=n_burn,
            nchain=n_chain,
            laglimit=[lag_limit]
        )

        # cybmod.show_hist()

        # Update progress bar in console ONLY
        print_progress(i + 1, n_iter, prefix='Progress:', suffix='Complete\n', length=40)

    logger.info("Sequence finished for config: %s", config_name)

    elapsed = time.time() - t
    logger.info("Time for config '%s': %.2f sec\n", config_name, elapsed)

    return elapsed


def main():
    """Main function: finds all .cfg files and processes them sequentially."""

    config_dir = '../light_curves'
    search_pattern = os.path.join(config_dir, '*.cfg')
    config_files = sorted(glob.glob(search_pattern))

    if not config_files:
        logger.error("No .cfg config files found in directory: %s", config_dir)
        sys.exit(1)

    logger.info("Found %d config file(s):", len(config_files))
    for cf in config_files:
        logger.info("  -> %s", cf)

    total_start = time.time()
    results = {}

    # Process each configuration file sequentially
    for config_path in config_files:
        config_name = os.path.basename(config_path)
        fh = None
        try:
            # 1. Load settings
            settings = load_config(config_path)

            # 2. Setup dynamic log file handler for this specific config
            log_path = settings['log_path']
            log_dir = os.path.dirname(log_path)

            # Create log directory if it doesn't exist
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            fh = logging.FileHandler(log_path)
            # IMPORTANT: Use standard formatter for the file, without color tags!
            fh.setFormatter(file_formatter)
            logger.addHandler(fh)

            # 3. Run the processing
            elapsed = run_javelin(settings, config_name)
            results[config_name] = elapsed

        except Exception as e:
            logger.error("ERROR processing config '%s': %s", config_name, str(e), exc_info=True)
            results[config_name] = None

        finally:
            # 4. Remove the file handler so the next config uses its own log file
            if fh is not None:
                logger.removeHandler(fh)
                fh.close()

    # --- Final Report (Prints to console) ---
    total_elapsed = time.time() - total_start
    logger.info("=" * filler_length)
    logger.info("ALL CONFIGS DONE")
    logger.info("=" * filler_length)

    for name, elapsed in results.items():
        if elapsed is not None:
            logger.info("  %s : %.2f sec", name, elapsed)
        else:
            logger.error("  %s : FAILED", name)

    logger.info("")
    logger.info("Total time: %.2f sec", total_elapsed)


if __name__ == '__main__':
    # Wrap in try/finally to gracefully restore sys.stdout on crashes
    try:
        main()
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr