# entro(py)

`entro(py)` is a thesis project for runtime entropy analysis of pseudo-random values generated during Doom gameplay.

The project uses **Crispy Doom**, **Freedoom**, **Frida**, **Docker** and a Python desktop application. The experiment collects RNG values while Doom is running, saves them as `.jsonl` logs, and then analyzes them with statistical metrics and visualizations.

## What is included

This repository contains two main parts:

* a Docker experiment environment for running Doom and collecting RNG data;
* a desktop analysis app for loading, visualizing and exporting the collected results.

Sample data extracted from Doom using this instrumentation setup can be found in:

`app/runs`

The compiled Windows application can be found in:

`app/dist/entro.exe`

## Project structure

`app/` contains the analysis application, parser, statistical pipeline and sample runs.

`scripts/` contains the experiment runner and the Frida hook.

`docker/` contains the Docker startup script.

`Dockerfile` builds the experiment environment.

`docker-compose.yml` simplifies running the container.

`start-desktop.ps1` opens the visible Docker desktop.

`run-experiment.ps1` starts the full experiment.

## Experiment details

The experiment compares RNG values collected from three gameplay situations:

* idle gameplay;
* scripted gameplay;
* human gameplay.

During each run, Frida observes selected Crispy Doom functions and records RNG values, timestamps and input-related events. The generated data is saved as `.jsonl` files and can be opened later in the `entro(py)` application.

## Running the experiment on Windows

Requirements:

* Windows 11;
* Docker Desktop;
* WSL 2 enabled;
* Linux containers enabled;
* PowerShell.

Open PowerShell in the project root folder.

If script execution is blocked, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Build the Docker image:

```powershell
docker compose build
```

Open the visible Docker desktop:

```powershell
.\start-desktop.ps1
```

Start the full experiment:

```powershell
.\run-experiment.ps1
```

The visible desktop opens through noVNC at:

```text
http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale
```

Generated experiment logs are saved in the local `runs/` folder.

## Viewing the results

Open the compiled app:

`app/dist/entro.exe`

Then click:

`[ load folder ]`

Select either:

`runs/`

or the included sample data folder:

`app/runs`

The application displays the results through the Overview, Analysis, Visualizations, Compare and Export pages.

## Analysis metrics

The application computes metrics for entropy, uniformity, dependency and sequence structure, including:

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

The results are intended for academic analysis, not cryptographic certification.

## Third-party components

This project uses Crispy Doom as the Doom source port used during the experiment.

Crispy Doom is developed by its respective authors, including Fabian Greffrath.

Original repository:

```text
https://github.com/fabiangreffrath/crispy-doom
```

License:

```text
GNU General Public License v2.0
```

This project also uses Freedoom as the free IWAD/game data file, so no commercial Doom WAD files are required.

Freedoom is developed by the Freedoom project contributors.

Original repository:

```text
https://github.com/freedoom/freedoom
```

License:

```text
BSD-style permissive license
```

This project does not claim ownership over Crispy Doom or Freedoom. They are used only as third-party components required to reproduce the experiment.

## Notes

The Frida hook observes runtime behaviour without modifying the original Doom source code or gameplay logic.

Docker is used only for experiment reproduction. The desktop application is used separately for analyzing the generated logs.

It is recommended to use the included sample data from app/runs when testing the application functionality. A complete experiment run can take approximately three hours, and the human gameplay condition requires direct user interaction for about one hour.

## Author

Anastasia Ciobanu

Bachelor’s thesis project — runtime entropy analysis and pseudo-randomness evaluation in interactive systems.
