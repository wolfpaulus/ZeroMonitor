# ZeroMonitor

Using the Raspberry Pi Zero 2 W for hardware monitoring

![zeromon1.jpeg](images/zeromon1.jpeg)

ZeroMonitor is a lightweight, customizable system monitor built for Raspberry Pi. 
It checks the health of remote computers agentless (via SSH) and visualizes the results 
using a strip of NeoPixels — one (or more) Pixels per host.

### Highlights
- Remote monitoring with SSH (secure, non-invasive, no agents required)
- Real-time visual feedback using NeoPixels
- Customizable modular design (clean OOP in Python) — easy to add new monitors
- CI/CD-style automatic updates with a simple polling strategy
- Automatic self-updating via Git and cron

## Example Monitors
- CPU temperature
- RAM usage
- Disk space

## Visual feedback via NeoPixels (e.g.):
- Green = healthy
- Yellow = warning
- Red = critical

## How It Works
The Pi connects to each host over SSH.
Gathers system metrics using remote commands.
Evaluates thresholds and maps state to color.
Updates the corresponding NeoPixel LED.

## ⚙️ Installation
Make sure SPI is enabled on the Raspberry Pi (via raspi-config) 
or check/add that following line to `/boot/firmware/config.txt`: dtparam=spi=on

```bash
git clone https://github.com/wolfpaulus/ZeroMonitor.git
cd ZeroMonitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo venv/bin/python" src/main.py &
```

# 🔄 CI/CD-Style Auto-Update

ZeroMonitor can automatically check for updates from GitHub and redeploy itself using a cron job.
For more details, see the [./zero/README.md](cicd/README.md) file.
