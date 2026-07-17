# -*- coding: utf-8 -*-
"""
===============================================================================
JAVELIN Histogram Tuner (GUI)
===============================================================================
Author: R. Uklein
Environment: Python 2.7 (legacy, targets JAVELIN v0.33) + Tkinter

Interactive tool to tune a single lag histogram and persist the settings to
hist.ini. The INI schema and the rendering are shared with the batch exporter
via `histlib`, so the preview matches the exported PNGs. Requires an X display.
===============================================================================
"""

import Tkinter as tk
import tkFileDialog
import tkMessageBox
import ConfigParser
import os
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
try:
    # Newer Matplotlib
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavigationToolbar
except ImportError:
    # Older Matplotlib (typical on Python 2.7 stacks)
    from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NavigationToolbar

import histlib


class HistTunerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JAVELIN Histogram Tuner")

        self.config_file = 'hist.ini'
        self.config = ConfigParser.SafeConfigParser()
        self.current_file = None

        # Dictionary to store Tkinter variables mapped to INI keys
        self.vars = {}

        # Single source of truth for the INI layout (shared with the batch).
        self.ini_structure = histlib.INI_SCHEMA

        self.load_config()
        self.build_gui()

    def load_config(self):
        """Loads configuration from hist.ini into Tkinter variables."""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            tkMessageBox.showwarning("Warning", "hist.ini not found. Using defaults.")

        for section, keys in self.ini_structure.items():
            if not self.config.has_section(section):
                self.config.add_section(section)

            for key, ktype in keys:
                if ktype == 'bool':
                    self.vars[key] = tk.BooleanVar()
                    try:
                        val = self.config.getboolean(section, key)
                    except ConfigParser.Error:
                        val = False
                    self.vars[key].set(val)
                    continue

                self.vars[key] = tk.StringVar()

                # Read value from config, with per-key fallbacks.
                try:
                    val = self.config.get(section, key)
                except ConfigParser.Error:
                    val = ""

                if not val:
                    if key == 'column' and self.config.has_section('Data'):
                        # Legacy layout: column lived in [Data] column_number.
                        try:
                            val = self.config.get('Data', 'column_number')
                        except ConfigParser.Error:
                            val = "3"
                    elif key == 'hist_color':
                        val = histlib.DEFAULT_HIST_COLOR
                    elif key == 'line_color':
                        val = histlib.DEFAULT_LINE_COLOR

                self.vars[key].set(val)

    def build_gui(self):
        """Constructs the GUI elements dynamically based on the INI structure."""
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top control panel (File open button and label)
        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        btn_open = tk.Button(top_frame, text="Open chain", command=self.open_file, width=15)
        btn_open.pack(side=tk.LEFT, padx=(0, 10))

        self.lbl_file = tk.Label(top_frame, text="No file selected", fg="blue")
        self.lbl_file.pack(side=tk.LEFT)

        # Body: settings on the left, live plot preview on the right.
        body_frame = tk.Frame(main_frame)
        body_frame.pack(fill=tk.BOTH, expand=True)

        settings_frame = tk.Frame(body_frame)
        settings_frame.pack(side=tk.LEFT, fill=tk.Y, anchor="n")

        plot_frame = tk.Frame(body_frame)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        col = 0
        row = 0
        for section, keys in self.ini_structure.items():
            frame = tk.LabelFrame(settings_frame, text=section, padx=5, pady=5)
            frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)

            r = 0
            for key, ktype in keys:
                tk.Label(frame, text=key + ":").grid(row=r, column=0, sticky="e", padx=2, pady=2)

                # Use Checkbutton for booleans, Entry for others
                if ktype == 'bool':
                    tk.Checkbutton(frame, variable=self.vars[key]).grid(row=r, column=1, sticky="w")
                else:
                    tk.Entry(frame, textvariable=self.vars[key], width=15).grid(row=r, column=1, sticky="w")
                r += 1

            col += 1
            if col >= 2:  # Maximum 2 columns of settings blocks
                col = 0
                row += 1

        # Embedded Matplotlib canvas for live preview (no separate window).
        self.figure = Figure(figsize=(6, 4.5))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar(self.canvas, plot_frame)
        toolbar.update()

        # Bottom panel with action buttons
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        btn_plot = tk.Button(bottom_frame, text="Plot hist", command=self.plot_hist, width=15, bg="lightgreen")
        btn_plot.pack(side=tk.LEFT, padx=(0, 10))

        btn_save = tk.Button(bottom_frame, text="Save config", command=self.save_config, width=15, bg="lightblue")
        btn_save.pack(side=tk.LEFT)

    def open_file(self):
        """Opens a file selection dialog to pick a .jav file."""
        init_dir = self.vars.get('data_dir').get() if 'data_dir' in self.vars else '.'
        filepath = tkFileDialog.askopenfilename(
            initialdir=init_dir,
            title="Select a .jav file",
            filetypes=(("JAV files", "*.jav"), ("All files", "*.*"))
        )
        if filepath:
            self.current_file = filepath
            self.lbl_file.config(text=os.path.basename(filepath))

    def save_config(self):
        """Saves current GUI field values back to the hist.ini file.

        Colors are persisted (in [Style]) so the batch exporter reuses them.
        """
        for section, keys in self.ini_structure.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for key, ktype in keys:
                val = str(self.vars[key].get())
                self.config.set(section, key, val)

        try:
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            tkMessageBox.showinfo("Success", "Configuration saved to hist.ini")
        except Exception as e:
            tkMessageBox.showerror("Error", "Could not save file:\n%s" % str(e))

    def get_val(self, key, ktype):
        """Convert a Tkinter variable to the type declared in INI_SCHEMA."""
        val = self.vars[key].get()
        if ktype == 'int':
            return int(val)
        if ktype == 'float':
            return float(val)
        if ktype == 'bool':
            return bool(val)
        return str(val)

    def _collect_cfg(self):
        """Assemble a typed config dict (same keys as histlib.load_hist_config)."""
        cfg = {}
        for section, keys in self.ini_structure.items():
            for key, ktype in keys:
                cfg[key] = self.get_val(key, ktype)
        return cfg

    def plot_hist(self):
        """Renders the histogram into the embedded canvas (live preview)."""
        if not self.current_file:
            tkMessageBox.showwarning("Warning", "Please open a chain file first!")
            return

        try:
            cfg = self._collect_cfg()
            col_index = cfg['column'] - 1

            data = np.loadtxt(self.current_file)
            column_data = data[:, col_index]

            # Shared renderer guarantees the preview matches the batch output.
            self.ax.clear()
            histlib.plot_histogram(self.ax, column_data, cfg)
            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            tkMessageBox.showerror("Plotting Error", "Error generating plot:\n%s" % str(e))


if __name__ == '__main__':
    root = tk.Tk()
    app = HistTunerApp(root)
    root.mainloop()
