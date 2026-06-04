import json
import pathlib
import re

# FILE PARSER (parser.py)
#
# contains the data-loading layer used by the application
# reads experiment logs and external data files, normalizes valid byte values,
# and prepares datasets for the statistical pipeline and GUI
#
# USAGE: automatically with run.py and entro.py

CONDITIONS = ["idle", "scripted", "human"]
ALLOWED_EXTENSIONS = {".jsonl", ".json", ".txt", ".csv", ".log", ".dat", ".bin", ".raw"}


# keeps only integer values that can be interpreted as one byte
def clean(values):
    out = []

    for value in values:
        try:
            x = int(value)

            if 0 <= x <= 255:
                out.append(x)

        except Exception:
            continue

    return out


# loads one .jsonl run file and separates RNG events from input events
def load_events(path):
    rng = []
    inputs = []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue

            if e.get("type") == "rng":
                rng.append(e)
            elif e.get("type") == "input":
                inputs.append(e)

    return rng, inputs


# loads all available run files for one condition
def load_condition(runs_dir, condition, n_runs):
    runs_dir = pathlib.Path(runs_dir)

    all_rng = []
    all_inputs = []

    for i in range(1, n_runs + 1):
        path = runs_dir / f"{condition}_run_{i}.jsonl"
        if not path.exists():
            print(f"[!] Missing: {path.name}")
            continue

        rng, inputs = load_events(path)
        all_rng.extend(rng)
        all_inputs.extend(inputs)

        print(f"[+] {path.name}: {len(rng)} rng, {len(inputs)} input events")

    return all_rng, all_inputs


# extracts RNG values, timestamps and uptimes, optionally filtered by function
def extract_values(rng, func=None):
    if func:
        rng = [e for e in rng if e.get("function") == func]

    values = [e["value"] for e in rng]
    timestamps = [e["timestamp"] for e in rng]
    uptimes = [e["uptime_ms"] for e in rng]

    return values, timestamps, uptimes


# reads RNG values directly from a .jsonl file
def load_jsonl(path):
    values = []

    with open(path, "r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            try:
                obj = json.loads(line)

            except Exception:
                continue

            if not isinstance(obj, dict):
                continue

            if obj.get("type") == "rng" and "value" in obj:
                values.append(obj["value"])

            elif "value" in obj and obj.get("type") not in {"input", "metadata", "hook_status"}:
                values.append(obj["value"])

    return clean(values)


# reads RNG values from .json lists or dictionaries
def load_json(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as file:
        obj = json.load(file)

    values = []

    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict) and "value" in item:
                values.append(item["value"])
            else:
                values.append(item)

    elif isinstance(obj, dict):
        if isinstance(obj.get("values"), list):
            values = obj["values"]

        elif isinstance(obj.get("rng"), list):
            for item in obj["rng"]:
                if isinstance(item, dict):
                    values.append(item.get("value"))
                else:
                    values.append(item)

    return clean(values)


# reads text, CSV-style numeric values or binary bitstreams converted to bytes
def load_text(path):
    text = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")
    compact = re.sub(r"\s+", "", text)

    if compact and set(compact).issubset({"0", "1"}) and len(compact) >= 8:
        values = []

        usable = len(compact) - (len(compact) % 8)

        for i in range(0, usable, 8):
            values.append(int(compact[i:i + 8], 2))

        return clean(values)

    return clean(re.findall(r"-?\d+", text))


# loads a supported data file and returns a clean byte-value sequence
def load_file(path):
    path = pathlib.Path(path)
    ext = path.suffix.lower()

    try:
        if ext == ".jsonl":
            return load_jsonl(path)

        if ext == ".json":
            return load_json(path)

        if ext in {".txt", ".csv", ".log", ".dat"}:
            return load_text(path)

        if ext in {".bin", ".raw"}:
            return list(path.read_bytes())

        values = load_jsonl(path)

        if values:
            return values

        values = load_text(path)

        if values:
            return values

        return list(path.read_bytes())

    except Exception:
        return []


# detects the dataset condition from the file name
def condition_name(path):
    name = pathlib.Path(path).name.lower()

    for condition in CONDITIONS:
        if condition in name:
            return condition

    return pathlib.Path(path).stem


# loads all supported files from a folder and groups them by condition
def load_folder(folder):
    folder = pathlib.Path(folder)
    data = {}

    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        values = load_file(path)

        if not values:
            continue

        key = condition_name(path)
        data.setdefault(key, []).extend(values)

    ordered = {}

    for condition in CONDITIONS:
        if condition in data:
            ordered[condition] = data[condition]

    for key, values in data.items():
        if key not in ordered:
            ordered[key] = values

    return ordered
