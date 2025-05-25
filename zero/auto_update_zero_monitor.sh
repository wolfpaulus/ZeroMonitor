#!/bin/bash
# ZeroMonitor Auto Update and Launcher

set -euo pipefail

REPO_URL="https://github.com/wolfpaulus/ZeroMonitor.git"
REPO_DIR="/opt/ZeroMonitor"
BRANCH="main"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/ZeroMonitor_backup_$TIMESTAMP"
LOG_PREFIX="[$(date '+%Y-%m-%d %H:%M:%S')]"
APP_PATH="$REPO_DIR/src/main.py"
LOG_FILE="/var/log/zero_monitor_runtime.log"

log() {
    echo "$LOG_PREFIX $1"
}

ensure_venv() {
    if [ ! -x "$REPO_DIR/venv/bin/python" ]; then
        log "== Setting up virtual environment =="
        python3 -m venv "$REPO_DIR/venv" --system-site-packages
        "$REPO_DIR/venv/bin/pip" install --upgrade pip
        "$REPO_DIR/venv/bin/pip" install -r "$REPO_DIR/requirements.txt"
    fi
    PYTHON="$REPO_DIR/venv/bin/python"
}
is_app_running() {
    pgrep -f "$APP_PATH" >/dev/null
}

start_app() {
    log "== Starting ZeroMonitor app =="
    nohup "$PYTHON" "$APP_PATH" >> "$LOG_FILE" 2>&1 &
    disown
}

cd /opt
log "== Checking for updates to ZeroMonitor =="

if [ ! -d "$REPO_DIR/.git" ]; then
    log "Initial clone..."
    git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
    ensure_venv
    start_app
    exit 0
fi

cd "$REPO_DIR"
git fetch origin "$BRANCH"
CHANGES=$(git diff --name-only HEAD origin/"$BRANCH" | grep '^src/' || true)

if [ -z "$CHANGES" ]; then
    log "No updates detected."
    if is_app_running; then
        log "App is already running."
    else
        log "App is NOT running — starting it..."
        ensure_venv
        start_app
    fi
    exit 0
fi

log "Updates detected. Applying update..."

log "== Stopping running app (if any) =="
pkill -f "$APP_PATH" || true

log "== Backing up current version =="
cd /opt
mv "$REPO_DIR" "$BACKUP_DIR"
# Keep only the 3 most recent backups, delete older ones
BACKUPS=(/opt/ZeroMonitor_backup_*)
NUM_BACKUPS=${#BACKUPS[@]}

if [ "$NUM_BACKUPS" -gt 3 ]; then
    log "Cleaning up old backups..."
    # Sort by modification time and delete oldest ones
    ls -dt /opt/ZeroMonitor_backup_* | tail -n +4 | while read -r old; do
        log "Deleting old backup: $old"
        rm -rf "$old"
    done
fi

log "== Cloning latest repo =="
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"

cd "$REPO_DIR"
ensure_venv
start_app
