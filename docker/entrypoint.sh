#!/usr/bin/env bash
set -e

export DISPLAY=:1
export SCREEN_WIDTH="${SCREEN_WIDTH:-1280}"
export SCREEN_HEIGHT="${SCREEN_HEIGHT:-720}"
export SCREEN_DEPTH="${SCREEN_DEPTH:-24}"
export DOOMWADDIR="/usr/share/games/doom"

cd /opt/entro

start_desktop() {
    echo "[+] Starting virtual display on ${DISPLAY}"

    Xvfb "${DISPLAY}" \
        -screen 0 "${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}" \
        -ac \
        +extension GLX \
        +render \
        -noreset &

    sleep 1

    echo "[+] Starting Openbox window manager"
    openbox >/tmp/openbox.log 2>&1 &

    echo "[+] Starting VNC server"
    x11vnc \
        -display "${DISPLAY}" \
        -forever \
        -shared \
        -nopw \
        -listen 0.0.0.0 \
        -xkb \
        -bg

    echo "[+] Starting noVNC on http://localhost:6080"
    websockify \
        --web=/usr/share/novnc/ \
        0.0.0.0:6080 \
        localhost:5900 >/tmp/novnc.log 2>&1 &

    sleep 1
}

run_experiment() {
    echo "[+] Starting full experiment through run_manager.py"
    echo "[+] Output will be written to /opt/entro/runs"
    python3 scripts/run_manager.py
}

show_menu() {
    echo ""
    echo "================================================"
    echo "  entro(py) Docker Experiment Environment"
    echo "================================================"
    echo "  noVNC: http://localhost:6080"
    echo ""
    echo "  1) Start full experiment"
    echo "  2) Start visible desktop only"
    echo "  3) Open shell"
    echo "================================================"
    echo ""

    read -r -p "Choose an option [1-3]: " choice

    case "${choice}" in
        1)
            run_experiment
            ;;
        2)
            echo "[+] Desktop is running. Open http://localhost:6080"
            tail -f /tmp/novnc.log
            ;;
        3)
            exec bash
            ;;
        *)
            echo "[!] Invalid option"
            exit 1
            ;;
    esac
}

start_desktop

case "${1:-menu}" in
    menu)
        show_menu
        ;;
    run)
        run_experiment
        ;;
    desktop)
        echo "[+] Desktop is running. Open http://localhost:6080"
        tail -f /tmp/novnc.log
        ;;
    shell)
        exec bash
        ;;
    *)
        echo "[!] Unknown command: $1"
        echo "Available commands: menu, run, desktop, shell"
        exit 1
        ;;
esac
