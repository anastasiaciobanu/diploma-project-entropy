````markdown
# entro(py) — Runtime Entropy Analysis of Doom RNG

`entro(py)` is a thesis project for collecting, analyzing and visualizing pseudo-random values generated at runtime by the Doom engine. The project uses Frida instrumentation, Crispy Doom and Freedoom to observe RNG behaviour during gameplay, then processes the collected data through a Python analysis application.

The project is organized into two main parts: a Docker-based experiment environment used for reproducible data collection, and a desktop application used for statistical analysis and visualization.

---

## Project purpose

The purpose of this project is to study how pseudo-random values behave in an interactive real-time system. The experiment compares RNG output collected from three gameplay conditions:

- idle gameplay;
- scripted gameplay;
- human gameplay.

The collected values are saved as structured `.jsonl` files and later analyzed using entropy, uniformity, correlation and sequence-complexity metrics.

---

## Project structure

`app/` contains the graphical analysis application.
`scripts/` contains the experiment runner and the Frida hook.
`docker/` contains the Docker entrypoint script.
`runs/` stores the generated experiment logs.
`Dockerfile` and `docker-compose.yml` define the reproducible experiment environment.

---

## Main components

### Docker experiment environment

The Docker container builds Crispy Doom, installs Freedoom, starts a visible Linux desktop through noVNC and runs the experiment manager. This allows the data collection process to be reproduced outside the original Linux development machine.

### Frida instrumentation

The `rng_hook.js` script attaches to selected Crispy Doom functions at runtime. It captures RNG values and selected input timing events, then sends them to `run_manager.py`.

The hook observes the running process without modifying the Doom source code or changing the gameplay logic.

### Analysis application

The `entro(py)` desktop application loads generated `.jsonl` files, computes statistical indicators and displays results through an interactive graphical interface. A compiled Windows executable is available in:

```text
app/dist/entro.exe
```

---

## Experiment workflow

The experiment follows this process:

1. Docker starts a reproducible Linux environment.
2. Crispy Doom is built inside the container.
3. Freedoom is used as the IWAD file.
4. `run_manager.py` starts Doom through Frida.
5. `rng_hook.js` captures RNG values and input timing events.
6. Runtime events are saved as `.jsonl` files in `runs/`.
7. The generated files are loaded into `entro(py)`.
8. The application computes and visualizes the statistical results.

---

## Requirements

For Windows usage:

* Windows 11;
* Docker Desktop;
* WSL 2 backend enabled;
* Linux containers enabled;
* PowerShell.

The compiled analysis application does not require a local Python installation.

---

## Running the experiment on Windows

Open PowerShell in the project root folder.

If PowerShell blocks local scripts, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Build the Docker image:

```powershell
docker compose build
```

Start only the visible Docker desktop:

```powershell
.\start-desktop.ps1
```

Start the full experiment:

```powershell
.\run-experiment.ps1
```

The noVNC interface is available at:

```text
http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale
```

---

## Viewing the results

After the experiment runs, the generated logs are saved in:

```text
runs/
```

To inspect the results:

1. Open `app/dist/entro.exe`.
2. Click `[ load folder ]`.
3. Select the `runs/` folder.
4. Use the Overview, Analysis, Visualizations, Compare and Export pages.

---

## Output files

Each experimental run generates a `.jsonl` file. Example files:

```text
idle_run_1.jsonl
scripted_run_1.jsonl
human_run_1.jsonl
state.json
```

The `.jsonl` files contain structured runtime events, including RNG values, timestamps, uptime values and input-related events.

---

## Statistical analysis

The application computes several metrics used to evaluate distribution, dependency, temporal structure and sequence complexity:

* Shannon entropy;
* chi-square uniformity test;
* Cramér’s V;
* runs test;
* serial correlation;
* autocorrelation;
* FFT spectrum;
* permutation entropy;
* mutual information;
* entropy over time.

The results are intended for academic analysis of pseudo-random behaviour in an interactive system.

---

## Notes and limitations

This project uses Freedoom and does not require commercial Doom WAD files.

The Frida hook observes runtime behaviour without modifying the original Doom source code.

The statistical analysis is exploratory and academic. It should not be interpreted as cryptographic certification.

The Docker environment is used for experiment reproduction, while the desktop application is used for analysis and visualization.

---

## Third-party components

This project uses third-party open-source components for the experiment environment.

### Crispy Doom

Crispy Doom is used as the Doom source port executed during the experiment. It is developed and maintained by its respective authors, including Fabian Greffrath.

Original repository:

```text
https://github.com/fabiangreffrath/crispy-doom
````

License:

```text
GNU General Public License v2.0 (GPL-2.0)
```

### Freedoom

Freedoom is used as the free IWAD/game data file for running the experiment without requiring commercial Doom WAD files. It is developed and maintained by the Freedoom project contributors.

Original repository:

```text
https://github.com/freedoom/freedoom
```

License:

```text
BSD-style permissive license
```

This project does not claim ownership over Crispy Doom or Freedoom. They are included or installed only as dependencies required to reproduce the experiment. All rights remain with their respective authors and contributors.

```


## Author

Anastasia Ciobanu

Bachelor’s thesis project — runtime entropy analysis and pseudo-randomness evaluation in interactive systems.

```
```
