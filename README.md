
# 🌌 Batch Processing Guide for JAVELIN

This set of scripts is designed for automated preparation of photometric data, batch execution of MCMC modeling in JAVELIN, and subsequent visualization of the results.

Original JAVELIN repository: https://github.com/nye17/javelin

**Tech stack:** `Python 2.7` | `Ubuntu 18.04` | `Tkinter` | `Matplotlib`

### 🔄 Workflow Overview

The full pipeline consists of 4 logical steps:

1. 🧹 **`preparation.py`** — clean raw data and create the required folder structure.
2. ⚙️ **`run-javelin.py`** — run batch computations (generate Markov chains).
3. 🎨 **`hist-tuner.py`** — GUI tool for adjusting histogram appearance.
4. 📊 **`chains2hist.py`** — batch export of histogram plots (PNG) for all files.

---

## 🐳 Running with Docker (Windows 10+)

Since these scripts depend on legacy **Python 2.7** and a graphical interface, the easiest way to run them is inside a Docker container.

### 1. Prepare the folder structure

Create a base folder, for example `C:\Javelin\`, where your Docker-related files will live. Inside it, create a folder named `mydata` — this will be your **working directory**, mounted into the container.

```text
📁 C:\Javelin\
 ├── 🐳 Dockerfile (and other image-related files)
 └── 📁 mydata\                   <-- This folder will be mounted into Docker
      └── 📁 object1\             <-- Folder for a specific object
           └── 📁 scripts\        <-- Your Python scripts
````

### 2. Start the container

Open a terminal (`cmd` or PowerShell), go to `C:\Javelin\`, and run:

```bash
cd C:\Javelin\
docker run -it --rm -v "%cd%\mydata:/workspace" -w /workspace/object1/scripts -e DISPLAY=host.docker.internal:0.0 ub18-jav:latest
```

**What each part does:**

- `-it` — starts the container in interactive mode, so you can type commands in its terminal.
- `--rm` — removes the container automatically when you exit, keeping your system clean.
- `-v "%cd%\mydata:/workspace"` — mounts your local `mydata` folder as `/workspace` inside the container. _All file changes are saved on your PC._
- `-w /workspace/object1/scripts` — opens the target working directory immediately after startup.
- `-e DISPLAY=...` — allows Docker to send graphical windows (for `hist-tuner.py`) to your display.

> 💡 **Important for Windows:** To use the GUI, you need an X server running on your machine, such as **VcXsrv** or **Xming**, configured to accept connections (for example, with _Disable access control_ enabled).

---

## 📂 Step 0: Place the input data

This workflow assumes that you process one object per directory (for example, `object1`). Create a `light_curves` folder at the same level as `scripts`, and place your raw `.txt` files there.

```text
📁 object1/
 ├── 📁 scripts/               <-- You are here
 │    ├── preparation.py
 │    └── ...
 └── 📁 light_curves/          <-- Put raw input files here (.txt)
      ├── my_object_cont.txt
      └── my_object_line.txt
```

> 📌 **Requirements for `.txt` files:**
> 
> - **3 columns:** MJD, Flux, Flux Error (space- or tab-separated)
> - **Comments:** lines starting with `#` are ignored
> - **File names:** continuum and line files must use the suffixes `_cont` and `_line`

---

## 🧹 Step 1: Prepare the data (`preparation.py`)

From inside the `scripts` folder, run the initial processing step:

```bash
python2 preparation.py
```

**This will automatically:**

1. Create the required folders (`jav_data`, `results`, `light_curves/_versions`).
2. Clean the raw `.txt` files and save them as **`.dat`** files in `jav_data/`.
3. Generate a default configuration file named **`start1.cfg`** in `light_curves/`.

---

## ⚙️ Step 2: Configure the MCMC parameters

Open the generated file `light_curves/start1.cfg`. You can copy it for multiple runs, for example: `runA.cfg`, `runB.cfg`.

```ini
[paths]
# Search patterns for converted light curves (exact filenames may also be used)
cont_pattern = ../jav_data/*_cont*.dat
line_pattern = ../jav_data/*_line*.dat

# Folder where output chains will be saved
chains_path = ../jav_data/chains_run1/

# Log file path
log_path = ../jav_data/logs/run1.log

[mcmc]
n_walkers = 100       # Number of walkers
n_burn = 500          # Burn-in length
n_chain = 500         # Chain length
lag_limit_min = 0     # Minimum lag limit
lag_limit_max = 10    # Maximum lag limit
n_iter = 50           # Number of generated output files (.jav)
```

> ⚠️ **Important:** If you run several different `.cfg` files, make sure to use different `chains_path` and `log_path` values in each one. Otherwise, newer runs will overwrite previous results.

---

## 🚀 Step 3: Run batch computations (`run-javelin.py`)

Once the `.dat` files are ready and the `.cfg` files are configured, start the computation:

```bash
python2 run-javelin.py
```

- The script will automatically find all `.cfg` files and process them one by one.
- A **progress bar** will be shown in the terminal.
- JAVELIN’s verbose output is suppressed and redirected into a `.log` file.
- The result is a folder such as `chains_run1`, filled with **`.jav`** files (Markov chains).

---

## 🎨 Step 4: Tune the histogram plots (`hist-tuner.py`)

Use the GUI to fine-tune the appearance of your histograms:

```bash
python2 hist-tuner.py
```

1. **Load data:** Click `Open chain` and select one representative `.jav` file.
2. **Set parameters:**
    - `column` = `3` (the lag column)
    - Adjust `x_min`, `x_max`, and `bins` (histogram resolution)
    - `lag_peak` — position of the vertical red line (peak marker)
3. **Preview:** Click `Plot hist`. A plot window will appear. Close it, adjust the values, and repeat until the plot looks right.
4. **Style:** You can set custom colors using HEX codes, for example `#601fb4`.
5. **Save:** Click `Save config`. The settings will be written to **`hist.ini`**.

---

## 📊 Step 5: Batch-generate histograms (`chains2hist.py`)

Once the plotting style is saved in `hist.ini`, generate plots for all files at once:

```bash
python2 chains2hist.py
```

The script will read the saved settings, find all `.jav` files, sort them naturally (`1, 2, ... 10`), and save high-quality `.png` plots into `results/run1/`.

---

## 🌳 Final project structure

After the full workflow, your project folder should look like this:

```text
📁 object1/
 ├── 📁 scripts/
 │    ├── preparation.py
 │    ├── run-javelin.py
 │    ├── hist-tuner.py
 │    ├── chains2hist.py
 │    └── hist.ini              <-- Your saved plotting preset
 │
 ├── 📁 light_curves/
 │    ├── 📁 _backup/           <-- Backup copies of raw data
 │    ├── start1.cfg            <-- Your MCMC config files
 │    ├── my_obj_cont.txt
 │    └── my_obj_line.txt
 │
 ├── 📁 jav_data/
 │    ├── my_obj_cont.dat       <-- Converted data
 │    ├── my_obj_line.dat
 │    ├── 📁 chains_run1/       <-- Generated Markov chains (.jav)
 │    │    └── javChain_1.jav
 │    └── 📁 logs/              <-- Computation logs
 │         └── run1.log
 │
 └── 📁 results/
      └── 📁 run1/              <-- Final plots
           ├── jav_Simulation_lag_chain1.png
           └── jav_Simulation_lag_chain2.png
```

---

## 🛠 Troubleshooting

|Problem / Error|Solution|
|---|---|
|**`No module named ConfigParser`**<br>or syntax errors|These scripts are written for Python 2. Make sure you run them with `python2`, not `python3`.|
|**`No files found matching pattern...`**|**During computation:** check the `cont_pattern` / `line_pattern` paths in your `.cfg` file.<br>**During plotting:** in the GUI tuner, check the `data_dir` and `file_pattern` fields, then click _Save config_.|
|**`Failed to process...`** (in `preparation.py`)|This is usually a permissions issue. Run `chmod -R 755 .` in the project root, or check folder permissions on the host system.|
|**`No module named Tkinter`**|The GUI library is not installed. On Ubuntu, install it with `sudo apt-get install python-tk`. _(It should already be present in the Docker image.)_|
|**`ValueError: could not convert string to float`**|A numeric field in the GUI contains an invalid character or extra space. Use a dot for decimals, for example `3.5`, not `3,5`.|
|**The GUI window does not open (in Docker)**|Make sure VcXsrv/Xming is running on Windows and that the correct `DISPLAY` value is passed to Docker.|

---

## Conclusion

This guide is intended as a quick way to estimate time delays between AGN photometric light curves. If the resulting histograms look promising, they should be examined more carefully: check for false peaks, choose sensible working limits, and estimate uncertainties. In a Bayesian framework, this is typically done using HPD intervals.

The code provided here targets Python 2 and is essentially legacy code. It is meant to run with JAVELIN v0.33. The JAVELIN author also provides a Python 3-compatible version. If you want to explore other delay estimation methods, you may also want to look at the pyPetal project.

For simulated light-curve generation and other advanced use cases, see the original JAVELIN documentation: [https://github.com/nye17/javelin](https://github.com/nye17/javelin)