import pathlib
import matplotlib.pyplot as plt

from pipeline import (
    shannon_entropy,
    autocorrelation,
    spectrum,
    value_distribution,
    entropy_over_time,
    permutation_entropy,
    mutual_information,
    cramers_v,
)

# PLOT GENERATION MODULE (plots.py)
#
# creates visual analysis outputs
# receives processed RNG values grouped by condition and saves
# plots for distribution, entropy, correlation and frequency-based
# behavior
#
# USAGE: automatically inside run.py and entro.py

COLORS = {
    "idle": "#4C72B0",
    "scripted": "#DD8452",
    "human": "#55A868",
    "P_Random": "#C44E52",
    "M_Random": "#8172B2",
}


# saves a generated matplotlib figure to the output directory
def _save(fig, out_dir, name):
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    path = out_dir / name
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[+] saved {path}")


# plots how often each RNG value appears in every condition
def plot_distributions(data, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5))

    for cond, values in data.items():
        bins, counts = value_distribution(values)
        ax.plot(bins, counts, label=cond, color=COLORS.get(cond))

    ax.set_title("RNG Value Distribution")
    ax.set_xlabel("Value")
    ax.set_ylabel("Count")
    ax.legend()

    _save(fig, out_dir, "01_distribution.png")


# compares the Shannon entropy score for each condition
def plot_entropy(data, out_dir):
    fig, ax = plt.subplots(figsize=(7, 5))

    labels = list(data.keys())
    values = [shannon_entropy(v) for v in data.values()]

    ax.bar(labels, values, color=[COLORS.get(x) for x in labels])
    ax.axhline(8.0, linestyle="--", color="red", label="max = 8 bits")

    ax.set_title("Shannon Entropy")
    ax.set_ylabel("Bits")
    ax.legend()

    _save(fig, out_dir, "02_entropy.png")


# shows whether RNG values are correlated with previous values at different lags
def plot_autocorrelation(data, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5))

    for cond, values in data.items():
        lags, coeffs = autocorrelation(values)
        ax.plot(lags, coeffs, label=cond, color=COLORS.get(cond))

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Autocorrelation")
    ax.set_xlabel("Lag")
    ax.set_ylabel("Correlation")
    ax.legend()

    _save(fig, out_dir, "03_autocorr.png")


# plots the FFT spectrum to reveal repeated frequency patterns in RNG sequences
def plot_spectrum(data, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5))

    for cond, values in data.items():
        freq, mag = spectrum(values)
        ax.plot(freq[1:], mag[1:], label=cond, color=COLORS.get(cond), linewidth=0.8)

    ax.set_title("FFT Spectrum")
    ax.set_xlabel("Normalized frequency")
    ax.set_ylabel("Magnitude")
    ax.legend()

    _save(fig, out_dir, "04_spectrum.png")


# tracks how entropy changes across consecutive windows of RNG values
def plot_entropy_over_time(data, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5))

    for cond, values in data.items():
        idx, ent = entropy_over_time(values)
        ax.plot(idx, ent, label=cond, color=COLORS.get(cond))

    ax.axhline(8.0, linestyle="--", color="red")
    ax.set_title("Entropy Over Time")
    ax.set_xlabel("Sample index")
    ax.set_ylabel("Entropy")
    ax.legend()

    _save(fig, out_dir, "05_entropy_time.png")


# compares the ordinal complexity of RNG sequences using permutation entropy
def plot_permutation_entropy(data, out_dir):
    fig, ax = plt.subplots(figsize=(7, 5))

    labels = list(data.keys())
    values = [permutation_entropy(v) for v in data.values()]

    ax.bar(labels, values, color=[COLORS.get(x) for x in labels])
    ax.axhline(1.0, linestyle="--", color="red", label="max = 1")

    ax.set_title("Permutation Entropy")
    ax.set_ylabel("Normalized score")
    ax.legend()

    _save(fig, out_dir, "06_permutation_entropy.png")


# measures dependency between RNG values separated by different lag distances
def plot_mutual_information(data, out_dir):
    fig, ax = plt.subplots(figsize=(10, 5))

    for cond, values in data.items():
        lags, mi = mutual_information(values)
        ax.plot(lags, mi, label=cond, color=COLORS.get(cond))

    ax.set_title("Mutual Information by Lag")
    ax.set_xlabel("Lag")
    ax.set_ylabel("Mutual information")
    ax.legend()

    _save(fig, out_dir, "07_mutual_information.png")


# visualizes the effect size of association inside each RNG value sequence
def plot_cramers_v(data, out_dir):
    fig, ax = plt.subplots(figsize=(7, 5))

    labels = list(data.keys())
    values = [cramers_v(v) for v in data.values()]

    ax.bar(labels, values, color=[COLORS.get(x) for x in labels])

    ax.set_title("Cramér's V Effect Size")
    ax.set_ylabel("Effect size")

    _save(fig, out_dir, "08_cramers_v.png")


# runs the complete plot generation workflow for all metrics
def generate_all_plots(data_by_condition, data_by_func_by_condition, out_dir):
    print("[*] Generating plots...")

    plot_distributions(data_by_condition, out_dir)
    plot_entropy(data_by_condition, out_dir)
    plot_autocorrelation(data_by_condition, out_dir)
    plot_spectrum(data_by_condition, out_dir)
    plot_entropy_over_time(data_by_condition, out_dir)
    plot_permutation_entropy(data_by_condition, out_dir)
    plot_mutual_information(data_by_condition, out_dir)
    plot_cramers_v(data_by_condition, out_dir)

    print("[+] Done")
