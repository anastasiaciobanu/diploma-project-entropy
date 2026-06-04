import math

import numpy as np

from parser import clean

"""
CORE ANALYSIS MODULE (pipeline.py)

receives byte-value sequences prepared by parser.py and calculates the metrics used for
entropy evaluation, uniformity testing, dependency detection and reporting.

USAGE: automatically with run.py and entro.py
"""

try:
    from scipy.stats import chisquare, norm
except Exception:
    chisquare = None
    norm = None

# computes Shannon entropy for the observed RNG value distribution
def shannon_entropy(values):
    values = clean(values)

    if not values:
        return 0.0

    counts = np.bincount(np.array(values, dtype=np.uint8), minlength=256)
    probabilities = counts[counts > 0] / len(values)

    return float(-np.sum(probabilities * np.log2(probabilities)))


# counts how often each possible byte value appears in the sequence
def distribution(values):
    values = clean(values)

    return (
        np.arange(256),
        np.bincount(np.array(values, dtype=np.uint8), minlength=256),
    )


# backward-compatible name used by the terminal plot module
def value_distribution(values):
    return distribution(values)


# tests how close the observed RNG distribution is to uniformity
def chi_square(values):
    values = clean(values)

    if not values or chisquare is None:
        return float("nan"), float("nan")

    _, counts = distribution(values)
    expected = np.full(256, len(values) / 256)

    statistic, p_value = chisquare(counts, f_exp=expected)

    return float(statistic), float(p_value)


# backward-compatible name used by the terminal analysis module
def chi_square_uniformity(values):
    return chi_square(values)


# computes effect size for deviation from a uniform distribution
def cramers_v(values):
    values = clean(values)

    if not values:
        return 0.0

    statistic, _ = chi_square(values)

    if math.isnan(statistic):
        return float("nan")

    return float(math.sqrt(statistic / (len(values) * 255)))


# applies a runs test to detect non-random ordering around the median
def runs_test(values):
    values = clean(values)

    if len(values) < 3:
        return 0.0, 1.0

    arr = np.array(values, dtype=float)
    signs = arr > np.median(arr)

    n1 = float(np.sum(signs))
    n2 = float(len(signs) - n1)
    n = n1 + n2

    if n1 == 0 or n2 == 0:
        return 0.0, 1.0

    runs = 1

    for i in range(1, len(signs)):
        if signs[i] != signs[i - 1]:
            runs += 1

    expected = (2 * n1 * n2) / n + 1
    variance = (2 * n1 * n2 * (2 * n1 * n2 - n)) / (n ** 2 * (n - 1))

    if variance <= 0:
        return 0.0, 1.0

    z_score = float((runs - expected) / math.sqrt(variance))

    if norm is None:
        p_value = float("nan")
    else:
        p_value = float(2 * (1 - norm.cdf(abs(z_score))))

    return z_score, p_value


# measures linear dependency between values separated by different lags
def autocorrelation(values, max_lag=50):
    values = clean(values)

    if len(values) <= max_lag + 2:
        return list(range(1, max_lag + 1)), [0.0] * max_lag

    x = np.array(values, dtype=float)
    x -= x.mean()

    lags = []
    scores = []

    for lag in range(1, max_lag + 1):
        a = x[:-lag]
        b = x[lag:]

        if np.std(a) == 0 or np.std(b) == 0:
            score = 0.0
        else:
            score = float(np.corrcoef(a, b)[0, 1])

        lags.append(lag)
        scores.append(score)

    return lags, scores


# computes lag-1 serial correlation between consecutive RNG values
def serial_correlation(values):
    values = clean(values)

    if len(values) < 3:
        return 0.0

    x = np.array(values, dtype=float)

    if np.std(x[:-1]) == 0 or np.std(x[1:]) == 0:
        return 0.0

    return float(np.corrcoef(x[:-1], x[1:])[0, 1])


# measures ordinal sequence complexity using normalized permutation entropy
def permutation_entropy(values, order=3, delay=1):
    values = clean(values)

    if len(values) < order + 1:
        return 0.0

    x = np.array(values, dtype=float)
    patterns = {}
    end = len(x) - (order - 1) * delay

    for i in range(end):
        pattern = tuple(np.argsort(x[i:i + order * delay:delay]))
        patterns[pattern] = patterns.get(pattern, 0) + 1

    counts = np.array(list(patterns.values()), dtype=float)
    probabilities = counts / counts.sum()

    entropy = -np.sum(probabilities * np.log2(probabilities))
    max_entropy = math.log2(math.factorial(order))

    return float(entropy / max_entropy)


# measures nonlinear dependency between two aligned byte sequences
def pairwise_mutual_information(a, b):
    a = np.array(clean(a), dtype=np.uint8)
    b = np.array(clean(b), dtype=np.uint8)

    if len(a) == 0 or len(a) != len(b):
        return 0.0

    hist = np.zeros((256, 256), dtype=float)

    for x, y in zip(a, b):
        hist[x, y] += 1

    pxy = hist / hist.sum()
    px = pxy.sum(axis=1)
    py = pxy.sum(axis=0)

    non_zero = pxy > 0
    denominator = px[:, None] * py[None, :]

    return float(np.sum(pxy[non_zero] * np.log2(pxy[non_zero] / denominator[non_zero])))


# returns mutual information scores for delayed versions of one sequence
def mutual_information_by_lag(values, max_lag=20):
    values = clean(values)

    if len(values) <= max_lag + 2:
        return list(range(1, max_lag + 1)), [0.0] * max_lag

    arr = np.array(values, dtype=np.uint8)
    lags = []
    scores = []

    for lag in range(1, max_lag + 1):
        lags.append(lag)
        scores.append(pairwise_mutual_information(arr[:-lag], arr[lag:]))

    return lags, scores


# compatibility wrapper for older code that called mutual_information(values)
def mutual_information(a, b=None, max_lag=20, bins=None):
    if b is None:
        return mutual_information_by_lag(a, max_lag=max_lag)

    return pairwise_mutual_information(a, b)


# computes the FFT spectrum to identify frequency-domain patterns
def fft_spectrum(values):
    values = clean(values)

    if len(values) < 2:
        return np.array([]), np.array([])

    x = np.array(values, dtype=float)
    x -= x.mean()

    return np.fft.rfftfreq(len(x)), np.abs(np.fft.rfft(x))


# backward-compatible name used by the terminal plot module
def spectrum(values):
    return fft_spectrum(values)


# computes Shannon entropy over sliding windows
def entropy_over_time(values, window=500, window_size=None):
    values = clean(values)

    if window_size is not None:
        window = window_size

    if len(values) < window:
        return [0], [shannon_entropy(values)]

    step = max(1, window // 2)

    xs = []
    ys = []

    for i in range(0, len(values) - window + 1, step):
        xs.append(i)
        ys.append(shannon_entropy(values[i:i + window]))

    return xs, ys


# converts a byte-value sequence to the bitstream format used by NIST export
def bitstream(values):
    return "".join(format(value, "08b") for value in clean(values))


# computes all metrics displayed by the GUI and export system
def analyze(values):
    values = clean(values)

    if not values:
        return {}

    arr = np.array(values, dtype=float)

    chi_stat, chi_p = chi_square(values)
    runs_z, runs_p = runs_test(values)

    _, autocorr_scores = autocorrelation(values)
    _, mi_scores = mutual_information_by_lag(values)

    return {
        "Samples": len(values),
        "Min": int(arr.min()),
        "Max": int(arr.max()),
        "Mean": float(arr.mean()),
        "Standard deviation": float(arr.std()),
        "Shannon entropy": shannon_entropy(values),
        "Permutation entropy": permutation_entropy(values),
        "Chi-square statistic": chi_stat,
        "Chi-square p-value": chi_p,
        "Cramér's V": cramers_v(values),
        "Runs test z-stat": runs_z,
        "Runs test p-value": runs_p,
        "Serial correlation": serial_correlation(values),
        "Max autocorr lag 1-50": max(abs(x) for x in autocorr_scores) if autocorr_scores else 0.0,
        "Mean mutual information": float(np.mean(mi_scores)) if mi_scores else 0.0,
    }


# prints the main statistical indicators for one RNG dataset
def full_summary(values, label=""):
    metrics = analyze(values)

    if not metrics:
        print(f"\n{label}: no valid samples")
        return

    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")

    print(f"  Samples           : {metrics['Samples']}")
    print(f"  Shannon entropy   : {metrics['Shannon entropy']:.6f}")
    print(f"  Permutation ent   : {metrics['Permutation entropy']:.6f}")
    print(f"  Cramér's V        : {metrics['Cramér\'s V']:.6f}")
    print(f"  Chi-square        : {metrics['Chi-square statistic']:.2f}  p={metrics['Chi-square p-value']:.6g}")
    print(f"  Runs test z       : {metrics['Runs test z-stat']:.4f}  p={metrics['Runs test p-value']:.6g}")
