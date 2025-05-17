#!/bin/bash

# === Configuration ===
REPO_URL="https://github.com/wolfpaulus/ZeroMonitor.git"
APP_DIR="ZeroMonitor"
VENV_DIR="venv"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="${APP_DIR}_backup_${TIMESTAMP}"
PYTHON_EXEC="python3"  # Update if using a different Python version

echo "=== ZeroMonitor Updater ==="

# === Step 1: Stop the running Python program ===
echo "[1/6] Stopping existing Python program..."
pkill -f "$APP_DIR" && echo "Process stopped." || echo "No matching process found."

# === Step 2: Backup current directory if it exists ===
if [ -d "$APP_DIR" ]; then
    echo "[2/6] Backing up current directory to $BACKUP_DIR"
    mv "$APP_DIR" "$BACKUP_DIR"
fi

# === Step 3: Clone fresh repo ===
echo "[3/6] Cloning repository..."
git clone "$REPO_URL" || { echo "Git clone failed. Exiting."; exit 1; }

# === Step 4: Set up virtual environment ===
cd "$APP_DIR" || { echo "Directory $APP_DIR not found. Exiting."; exit 1; }
echo "[4/6] Creating virtual environment..."
$PYTHON_EXEC -m venv "$VENV_DIR" --system-site-packages
source "$VENV_DIR/bin/activate" || { echo "Failed to activate virtualenv. Exiting."; exit 1; }

# === Step 5: Install dependencies ===
echo "[5/6] Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt || { echo "Failed to install requirements. Exiting."; exit 1; }

# === Step 6: Launch the program with SPI access ===
echo "[6/6] Launching program with SPI access..."

# Run as superuser to access /dev/spidev*
sudo "$VENV_DIR/bin/python" src/main.py &

echo "ZeroMonitor started."