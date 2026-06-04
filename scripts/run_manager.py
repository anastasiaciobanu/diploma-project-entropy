import os
import frida
import json
import time
import pathlib

# RUN MANAGER FOR EXPERIMENTS (run_manager.py)
#
# automates the data collection stage
# it starts Doom through Frida, loads the RNG instrumentation script,
# records events into .jsonl files, and repeats the process for each
# condition: idle, scripted and human
#
# USAGE: terminal only, doesn't require venv, only runs in the docker image

# PROJECT PATHS
SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# GAME CONFIG
GAME = PROJECT_ROOT / "doom/build/crispy-doom/build/src/crispy-doom"
IWAD = "freedoom1.wad"

# Demo lump used by the scripted condition.
# "demo1" is included inside freedoom1.wad.
DEMO = "demo1"

# FRIDA SCRIPTS
RNG_SCRIPT = SCRIPT_DIR / "rng_hook.js"

# OUTPUT
OUTPUT_DIR = PROJECT_ROOT / "runs"
OUTPUT_DIR.mkdir(exist_ok=True)

STATE_FILE = OUTPUT_DIR / "state.json"

# EXPERIMENT SETTINGS
RUN_DURATION = 300      # seconds (5 minutes)
COOLDOWN     = 3        # seconds between runs

RUNS = {
    "idle":     10,
    "scripted": 10,
    "human":    10,
}

# loads the saved experiment progress, allowing interrupted sessions to resume
def load_state():

    if not STATE_FILE.exists():
        return {"condition": None, "run_id": 0}

    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("[!] state.json is corrupted — resetting to fresh state.")
        return {"condition": None, "run_id": 0}


# saves the current condition and run number after a run starts
def save_state(condition, run_id):

    with open(STATE_FILE, "w") as f:
        json.dump({"condition": condition, "run_id": run_id}, f, indent=4)

# creates the Frida message handler used to process events from rng_hook.js
def make_handler(logfile):

    def on_message(message, data):

        msg_type = message.get("type")

        if msg_type == "log":
            print(f"[js] {message.get('payload')}")

        elif msg_type == "error":
            print(f"[js:error] {message.get('description')}")
            print(f"[js:error] {message.get('stack')}")

        elif msg_type == "send":
            # high-frequency RNG data is written to file to avoid terminal spam
            payload = message["payload"]
            with open(logfile, "a") as f:
                f.write(json.dumps(payload) + "\n")

        else:
            print(f"[frida] {message}")

    return on_message

# loads a Frida JS hook into the attached Doom process
def load_script(session, path, handler):

    with open(path) as f:
        source = f.read()

    script = session.create_script(source)
    script.on("message", handler)
    script.load()

    print(f"[+] Loaded: {path.name}")

    return script

# builds the command-line arguments used to start Doom for each condition
def build_spawn_args(condition):

    base = [str(GAME), "-iwad", IWAD]

    if condition == "scripted":
        return base + ["-playdemo", DEMO]

    return base

# runs one complete experimental session and stores its collected events
def run_experiment(condition, run_id):

    logfile = OUTPUT_DIR / f"{condition}_run_{run_id}.jsonl"

    print("\n================================================")
    print(f"  STARTING {condition.upper()} RUN {run_id}")
    print("================================================")

    device = frida.get_local_device()

    # SPAWN
    args = build_spawn_args(condition)

    pid = device.spawn(args)

    print(f"[+] Spawned PID={pid}  args={args}")

    # ATTACH + LOAD RNG HOOK
    session = device.attach(pid)
    handler = make_handler(logfile)

    print("[+] Loading rng_hook.js")
    load_script(session, RNG_SCRIPT, handler)

    if condition == "scripted":
        print(f"[+] Scripted condition: demo playback ({DEMO})")
        print("[+] No input injection needed — engine replays demo internally")
    elif condition == "human":
        print("[+] Human condition: play normally in the game window")
    else:
        print("[+] Idle condition: no input, collecting baseline RNG")

    # RESUME + SAVE STATE
    device.resume(pid)

    print(f"[+] Game resumed — collecting for {RUN_DURATION}s")

    save_state(condition, run_id)

    # COLLECTION LOOP
    start = time.time()

    try:

        while time.time() - start < RUN_DURATION:

            # stops early if the scripted demo finishes before the time limit
            if condition == "scripted":
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    print("\n[+] Demo ended — process exited cleanly.")
                    break

            remaining = int(RUN_DURATION - (time.time() - start))
            print(f"\r[+] Remaining: {remaining}s", end="", flush=True)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        print("[!] Progress saved to state.json — rerun to resume")
        raise

    finally:

        print("\n[+] Ending run")

        # detach Frida
        try:
            session.detach()
            print("[+] Session detached")
        except Exception as e:
            print(f"[!] Detach error: {e}")

        # kill game if still running
        try:
            device.kill(pid)
            print("[+] Game process terminated")
        except Exception as e:
            print(f"[+] Process already gone: {e}")

        print(f"[+] Cooldown: {COOLDOWN}s")
        time.sleep(COOLDOWN)

# coordinates all configured experimental conditions and run repetitions
def main():

    print("================================================")
    print("  Runtime Entropy Experiment Manager")
    print("================================================")

    print("[+] Loading saved state")
    state = load_state()

    resumed = False

    for condition, total_runs in RUNS.items():

        start_run = 1

        # resume support
        if not resumed and state["condition"] == condition:
            start_run = state["run_id"] + 1
            resumed = True
            print(f"[+] Resuming from {condition} run {start_run}")

        elif state["condition"] is not None and not resumed:
            continue

        for run_id in range(start_run, total_runs + 1):
            run_experiment(condition, run_id)

    save_state(None, 0)

    print("\n================================================")
    print("  ALL EXPERIMENTS COMPLETED")
    print("================================================")

if __name__ == "__main__":
    main()

