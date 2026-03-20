# -*- coding: utf-8 -*-
import Tkinter as tk
import tkFileDialog
import tkMessageBox
import ConfigParser
import os
import numpy as np
import matplotlib.pyplot as plt

class HistTunerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JAVELIN Histogram Tuner")
        
        self.config_file = 'hist.ini'
        self.config = ConfigParser.SafeConfigParser()
        self.current_file = None

        # Dictionary to store Tkinter variables mapped to INI keys
        self.vars = {}

        # INI file structure definition: {Section: [(Key, Type), ...]}
        # Removed the 'Data' section and moved 'column' to 'Plot'
        # Added 'hist_color' and 'line_color' to 'Style' for GUI-only tuning
        self.ini_structure = {
            'Path': [('data_dir', 'str'), ('file_pattern', 'str'), ('output_dir', 'str')],
            'Plot': [('column', 'int'), ('bins', 'int'), ('x_min', 'float'), ('x_max', 'float'), 
                     ('y_min', 'float'), ('y_max', 'float'), ('dpi', 'int')],
            'Annotations': [('agn_name', 'str'), ('comment', 'str'), ('x_label', 'str'), 
                            ('y_label', 'str'), ('lag_peak', 'float'), ('lag_label', 'str'), 
                            ('lab_font_size', 'int'), ('title_font_size', 'int')],
            'Style': [('yaxis_right', 'bool'), ('hist_color', 'str'), ('line_color', 'str')]
        }

        self.load_config()
        self.build_gui()

    def load_config(self):
        """Loads configuration from hist.ini into memory."""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            tkMessageBox.showwarning("Warning", "hist.ini not found. Using defaults.")

        # Iterate over sections and keys to populate Tkinter variables
        for section, keys in self.ini_structure.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            for key, ktype in keys:
                # Initialize Tkinter variable based on the expected type
                if ktype == 'bool':
                    self.vars[key] = tk.BooleanVar()
                    try:
                        val = self.config.getboolean(section, key)
                    except ConfigParser.Error: 
                        val = False
                    self.vars[key].set(val)
                else:
                    self.vars[key] = tk.StringVar()
                    
                    # Set default hex colors for GUI-only fields (do not read from INI)
                    if key == 'hist_color':
                        self.vars[key].set('#601fb4')
                        continue
                    if key == 'line_color':
                        self.vars[key].set('#ff0000')  # Default red
                        continue

                    # Try reading value from the config file
                    try:
                        val = self.config.get(section, key)
                    except ConfigParser.Error: 
                        # Fallback for column if it's still in the old [Data] section
                        if key == 'column' and self.config.has_section('Data'):
                            try:
                                val = self.config.get('Data', key)
                            except ConfigParser.Error:
                                val = "3"
                        else:
                            val = ""
                    
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

        # Frames for settings sections (Grid layout)
        settings_frame = tk.Frame(main_frame)
        settings_frame.pack(fill=tk.BOTH, expand=True)

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
            if col >= 2:  # Maximum 3 columns of settings blocks
                col = 0
                row += 1

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
        """Saves current GUI field values back to the hist.ini file."""
        for section, keys in self.ini_structure.items():
            for key, ktype in keys:
                # Skip saving colors to the INI file
                if key in ['hist_color', 'line_color']:
                    continue
                
                val = str(self.vars[key].get())
                self.config.set(section, key, val)

        try:
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            tkMessageBox.showinfo("Success", "Configuration saved to hist.ini")
        except Exception as e:
            tkMessageBox.showerror("Error", "Could not save file:\n%s" % str(e))

    def get_val(self, key, ktype):
        """Helper function to convert Tkinter string variables to appropriate Python types."""
        val = self.vars[key].get()
        if ktype == 'int': return int(val)
        if ktype == 'float': return float(val)
        if ktype == 'bool': return bool(val)
        return str(val)

    def plot_hist(self):
        """Reads the selected file and plots the histogram using current GUI fields."""
        if not self.current_file:
            tkMessageBox.showwarning("Warning", "Please open a chain file first!")
            return

        try:
            # Extract parameters directly from GUI
            col_index = self.get_val('column', 'int') - 1
            bins = self.get_val('bins', 'int')
            x_min = self.get_val('x_min', 'float')
            x_max = self.get_val('x_max', 'float')
            y_min = self.get_val('y_min', 'float')
            y_max = self.get_val('y_max', 'float')
            
            agn_name = self.get_val('agn_name', 'str')
            comment = self.get_val('comment', 'str')
            x_label = self.get_val('x_label', 'str')
            y_label = self.get_val('y_label', 'str')
            lag_peak = self.get_val('lag_peak', 'float')
            lag_label = self.get_val('lag_label', 'str')
            lab_font_size = self.get_val('lab_font_size', 'int')
            title_font_size = self.get_val('title_font_size', 'int')
            
            yaxis_right = self.get_val('yaxis_right', 'bool')
            hist_color = self.get_val('hist_color', 'str')
            line_color = self.get_val('line_color', 'str')

            # Read the selected chain data
            data = np.loadtxt(self.current_file)
            column_data = data[:, col_index]

            # Create plot (opens in a separate interactive Matplotlib window)
            fig, ax = plt.subplots()
            
            # Plot using custom colors from GUI
            ax.hist(column_data, bins=bins, color=hist_color, edgecolor='black')
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
            ax.axvline(x=lag_peak, color=line_color, linestyle='--')
            
            # Add text annotation
            ax.text(lag_peak + 0.1, y_max * 0.9, lag_label, 
                    fontsize=lab_font_size, horizontalalignment='left')
            
            # Labels and title
            ax.set_xlabel(x_label, fontsize=lab_font_size)
            ax.set_ylabel(y_label, fontsize=lab_font_size)
            
            full_title = "JAVELIN analysis for %s\n%s" % (agn_name, comment)
            ax.set_title(full_title, fontsize=title_font_size)

            # Move Y-axis to the right side if requested
            if yaxis_right:
                ax.yaxis.tick_right()
                ax.yaxis.set_label_position("right")

            plt.tight_layout()
            plt.show()  # Display the plot to the user

        except Exception as e:
            tkMessageBox.showerror("Plotting Error", "Error generating plot:\n%s" % str(e))


if __name__ == '__main__':
    root = tk.Tk()
    app = HistTunerApp(root)
    root.mainloop()