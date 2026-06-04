import pathlib

from parser import load_condition, extract_values
from pipeline import full_summary
from plots import generate_all_plots

# TERMINAL-ONLY MODULE MANAGER (run.py)
#
# earlier terminal-only version of the analysis workflow 
# loads the collected .jsonl runs, extracts RNG values for each condition, prints statistical summaries
# in the terminal, and generates the analysis plots
#
# USAGE: terminal only, doesn't require venv

ROOT = pathlib.Path(__file__).parent
RUNS = ROOT / "runs"
OUT  = ROOT / "analysis"

CONDITIONS = ["idle", "scripted", "human"]
N_RUNS = 10


data = {}
func_data = {}

print("[*] Loading data...")

# loads RNG and input events for each condition
for c in CONDITIONS:
    rng, inputs = load_condition(RUNS, c, N_RUNS)

    if not rng:
        continue

    all_v, _, _ = extract_values(rng)
    p_v, _, _ = extract_values(rng, "P_Random")
    m_v, _, _ = extract_values(rng, "M_Random")

    data[c] = all_v
    func_data[c] = {
        "P_Random": p_v,
        "M_Random": m_v
    }


print("\n[*] Summary")

# prints terminal summaries for every condition that contains valid data
for c, v in data.items():
    full_summary(v, c)


# creates plots for the dataset and the separate RNG functions
generate_all_plots(data, func_data, OUT / "plots")

print("[+] Done")
