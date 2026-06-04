````markdown
# entro(py)

`entro(py)` is a bachelor’s thesis project for runtime entropy analysis and pseudo-randomness evaluation in Doom-based gameplay sessions. The project collects RNG values from Crispy Doom using Frida instrumentation, stores the captured data as structured experiment logs, and analyzes the results through a Python desktop application.

The project combines a reproducible Docker experiment environment with a graphical Windows analysis tool. Docker is used to run the experiment in a controlled Linux environment, while the desktop application is used to load, visualize and export the generated results.

---

## What this project does

The experiment observes pseudo-random values generated during three gameplay conditions:

- idle gameplay;
- scripted gameplay;
- human gameplay.

During each run, Frida hooks selected Crispy Doom functions and records RNG values, timestamps and selected input-related events. The collected data is saved as `.jsonl` files in the `runs/` folder.

The generated files can then be opened in the `entro(py)` application, where the data is analyzed using entropy, uniformity, correlation and sequence-complexity metrics.

---

## Main features

- Runtime RNG extraction using Frida.
- Reproducible experiment environment using Docker.
- Crispy Doom built automatically inside the container.
- Freedoom used as the free game data file.
- Visible Doom session through noVNC.
- JSONL logging for each experimental run.
- Windows desktop application for analysis and visualization.
- Export options for reports, metrics, summaries and bitstreams.

---

## Project structure

The main project folders are:

- `app/` — contains the `entro(py)` analysis application.
- `scripts/` — contains the experiment runner and Frida hook.
- `docker/` — contains the Docker entrypoint script.
- `runs/` — stores generated experiment logs.
- `Dockerfile` — builds the experiment environment.
- `docker-compose.yml` — simplifies running the Docker container.
- `start-desktop.ps1` — starts the visible Docker desktop.
- `run-experiment.ps1` — starts the full experiment.

The compiled Windows application is located at:

```text
app/dist/entro.exe
````

---

## Running the experiment on Windows

The Docker experiment requires Windows 11, Docker Desktop, WSL 2 and Linux containers enabled.

Open PowerShell in the project root folder. If script execution is blocked, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Build the Docker image:

```powershell
docker compose build
```

To open only the visible Docker desktop, run:

```powershell
.\start-desktop.ps1
```

To start the full experiment, run:

```powershell
.\run-experiment.ps1
```

The visible desktop is available in the browser at:

```text
http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale
```

The experiment output is saved automatically in the local `runs/` folder.

---

## Viewing the results

After the experiment has generated data, open:

```text
app/dist/entro.exe
```

Then click `[ load folder ]` and select the `runs/` folder.

The application displays the results through several pages:

* Overview;
* Analysis;
* Visualizations;
* Compare;
* Export.

The app can also export JSON reports, CSV metrics, text summaries and binary bitstreams.

---

## Analysis metrics

The analysis pipeline includes several statistical indicators used to evaluate distribution, temporal dependency and sequence complexity:

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

## Third-party components

This project uses Crispy Doom as the Doom source port used during the experiment.

Crispy Doom is developed and maintained by its respective authors, including Fabian Greffrath.
Original repository: https://github.com/fabiangreffrath/crispy-doom
License: GNU General Public License v2.0.

This project also uses Freedoom as the free IWAD/game data file, so no commercial Doom WAD files are required.

Freedoom is developed and maintained by the Freedoom project contributors.
Original repository: https://github.com/freedoom/freedoom
License: BSD-style permissive license.

This project does not claim ownership over Crispy Doom or Freedoom. They are used only as third-party components required to reproduce the experiment.

---

## Notes

The Frida hook observes runtime behaviour without modifying the Doom source code or changing the gameplay logic.

The Docker environment is used for experiment reproduction. The desktop application is used separately for loading and analyzing the generated logs.

The statistical analysis is exploratory and academic. It should not be interpreted as cryptographic certification.

---

## Author

Anastasia Ciobanu

Bachelor’s thesis project — runtime entropy analysis and pseudo-randomness evaluation in interactive systems.

```
```
