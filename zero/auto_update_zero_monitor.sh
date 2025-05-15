#!/bin/bash

set -e

REPO_URL="https://github.com/wolfpaulus/ZeroMonitor.git"
REPO_DIR="/opt/ZeroMonitor"
BACKUP_DIR="${REPO_DIR}_$(date +%Y%m%d_%H%M%S)_backup"
BRANCH="main"

cd "/opt"
echo "== Checking for updates to ZeroMonitor =="

if [ ! -d "$REPO_DIR" ]; then
    echo "Cloning for the first time..."
    git clone --depth 1 --branch $BRANCH "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
else
    cd "$REPO_DIR"
    echo "Fetching latest changes..."
    git fetch origin $BRANCH
    CHANGES=$(git diff HEAD origin/$BRANCH --name-only | grep '^src/')
    if [ -z "$CHANGES" ]; then
        echo "No changes in src/, skipping update."
        exit 0
    fi
    echo "Changes found: $CHANGES"
fi

echo "== Stopping running app (if any) =="
pkill -f ZeroMonitor/app.py || true

echo "== Backing up current version =="
cd "/opt"
mv "$REPO_DIR" "$BACKUP_DIR"

echo "== Cloning latest repo =="
git clone --depth 1 --branch $BRANCH "$REPO_URL" "$REPO_DIR"

cd "$REPO_DIR"

echo "== Setting up virtual environment =="
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "== Launching app =="
sudo -E env "PATH=$PATH" venv/bin/python src/app.py &
