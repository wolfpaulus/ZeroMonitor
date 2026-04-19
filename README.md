[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![run-tests](https://github.com/wolfpaulus/ZeroMonitor/actions/workflows/python-test.yml/badge.svg)](https://github.com/wolfpaulus/ZeroMonitor/actions/workflows/python-test.yml)

# ZeroMonitor

Using the Raspberry Pi Zero 2 W for hardware monitoring

![mon2.jpg](images/mon2.jpg)
_ZeroMonitor with 4x8-NeoPixels_

ZeroMonitor is a lightweight, customizable system monitor built for Raspberry Pi Zero 2 W.
It checks the health of remote computers agentless (via SSH) and visualizes the results
using a strip of NeoPixels — one (or more) Pixels per host.

### Highlights
- Remote monitoring with SSH (secure, non-invasive, no agents required)
- Real-time visual feedback using NeoPixels
- Customizable modular design (clean OOP in Python) — easy to add new monitors
- CI/CD-style automatic updates with a simple polling strategy (cron):
  - Check for updates from GitHub
  - Redeploy itself if an update is available

## 💵 BOM (Bill of Materials) < $50
- [Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) $15
- [NeoPixels, e.g. 8x NeoPixel sticks](https://www.waveshare.com/product/raspberry-pi/hats/led-buttons/rgb-led-hat.htm) $11
- [Power supply - 5V, 2A recommended](https://www.raspberrypi.com/products/micro-usb-power-supply/) $9
- (reasonably fast) MicroSD card (8GB or larger) $8
- (optional) [Pi Zero Case for Waveshare](https://thepihut.com/products/pi-zero-case-for-waveshare-2-13-eink-display) $9


## 🌡️ Example Monitors
- CPU temperature
- CPU usage
- RAM usage
- Disk space
- Active Streamlit sessions

## 🔵🟢🟠🔴🟣 Visual feedback via NeoPixels (e.g.):
- Blue: low/idle
- Turquoise: below normal
- Green: medium/normal
- Orange: above medium
- Red: high
- Pink: critical
- Black/off: offline

![mon4.jpg](images/mon4.jpg)
_ZeroMonitor with 4x8-NeoPixels_

## 🧭 How It Works
The Pi connects to the monitored hosts over SSH.
Gathers system metrics using remote commands.
Evaluates thresholds and maps state to color.
Updates the corresponding NeoPixel LED.

## 🚀 Getting Started
1. Fork the repository and clone it to your laptop.
2. Set up the configuration file with your hosts and thresholds (see [Configuration](#-configuration)).
3. Using [Raspberry Pi Imager](https://www.raspberrypi.com/software/), create a bootable SD card with Raspberry Pi OS and set up SSH access.


## ⚙️ Configuration
### create a `/home/zero/.ssh/authorized_keys` file on each monitored hosts
For the Pi to ssh into the monitored hosts, SSH key-based authentication is required. This involves [generating an SSH key pair](https://www.ssh.com/academy/ssh/keygen) on the Pi, creating a `zero` user, and adding the public key to the `/home/zero/.ssh/authorized_keys` file on each monitored host. This way, the Pi can connect securely without needing passwords.
__That should be the only setup required on the monitored hosts — no additional software or agents are needed, making it a non-invasive monitoring solution.__

### create a `/root/.ssh/config` file on the Pi Zero
Since the monitoring script will be running as root (to access the GPIO pins for the NeoPixels) and because it's lauche as a cron job, you need to set up the SSH config for the root user on the Pi. This involves creating a `/root/.ssh/config` file that defines the hosts you want to monitor, along with their IP addresses, usernames, and SSH key paths. This allows the monitoring script to easily connect to the hosts using simple hostnames defined in the SSH config.
To simplify SSH connections, you can set up the `/root/.ssh/config` like shown below, which allows you to use simple hostnames (e.g. `ssh alpha`) instead of full IP addresses and options every time. No usernames, ports, or identity files need to be specified in the code — just the hosts like `alpha` and `beta` defined in the SSH config.

#### Example SSH Config
```plaintext
Host alpha
    User zero
    Port 22
    HostName 192.168.200.16
    IdentityFile ~/.ssh/id_rsa

Host beta
    User zero
    Port 22
    HostName 192.168.200.17
    IdentityFile ~/.ssh/id_rsa
```

### Monitoring Configuration
The monitoring configuration is defined in a YAML file (e.g. `config.yaml`) that specifies the hosts to monitor, the metrics to check, and the thresholds for each state. This allows for easy customization without modifying the code. Each host can have multiple monitors (e.g. CPU temp, CPU usage, RAM usage) with their own thresholds and corresponding colors.

![RGB-LED-HAT-size.jpg](images/RGB-LED-HAT-size.jpg)

#### Mode
The 4 rows 8 columns of NeoPixels can be used to monitor:
- mode = 1 : "single host mode" with up to 32 metrics for one host (one pixel per metric)
- mode = 2 : "horizontal mode" with up to 4 hosts with 8 metrics each (one row per host
- mode = 3 : "vertical mode" with up to 8 hosts with 4 metrics each (one column per host)
- mode = 4 : up to 32 hosts with one metric each (one pixel per host)


### Example Config
```yaml
# Configuration file for monitoring systems' health and performance
displays:
  neopixel:
    brightness: 127 # Brightness of the strip (24-255)
    sensor_timeout: 1 # Pause after probing a sensor
    off_: "20:00" # Turn off at 20:00, on at 6:30
    on_: "6:30" # Turn on at 6:30, off at 8:00
    mode: 3 # up to 8 hosts in vertical mode

sensors: # All sensors to monitor
  CpuUsage:
    name: CpuUsage
    description: CPU usage percentage
    cmd: mpstat -P ALL 1 1 | awk '$1 == "Average:" && $2 == "all" { print 100 - $NF }' # CPU usage percentage
    values: # idle, normal, high
      - 3
      - 15
      - 30

  CpuTemperature:
    name: CpuTemperature
    description: CPU package temperature in Celsius
    cmd: cat /sys/class/thermal/thermal_zone0/temp # CPU package temperature
    values: # low, normal, high
      - 50
      - 62
      - 75

hosts: # List of hosts to monitor
  - hostname: alpha # Intel NUC Core i5
    details: NUC CoreI5 16GB 256GB SSD
    CpuTemperature:
      cmd: cat /sys/class/thermal/thermal_zone2/temp # CPU package temperature

  - hostname: beta # Intel NUC Core i3
    details: NUC CoreI3 16GB 128GB SSD
    CpuTemperature:
      cmd: cat /sys/class/thermal/thermal_zone2/temp # CPU package temperature
```

![zeromon1.jpeg](images/zeromon1.jpeg)
_-1st prototype of ZeroMonitor with two 8-NeoPixels sticks-_


## ⚙️ Installation
1. Edit the `monitor.yaml` configuration file with your hosts and thresholds.
2. Edit the `cicd/auto_update.sh` script to point to your GitHub repo (replace `<your-username>` with your actual GitHub username).
3. You have now two options to install ZeroMonitor on the Pi:

### Ansible Playbook
This ansible playbook can be used to install ZeroMonitor on a Raspberry Pi:
[./ansible/playbooks/setup-zero_mon.yml]()

ZeroMonitor can automatically check for updates from GitHub and redeploy itself using a cron job.
For more details, see the [./cicd/README.md](cicd/README.md) file.

### Manual Bootstrap
1. ssh into the Pi
2. Look at the ansible playbook for the required steps:
    - install dependencies
    - copy ssh key
    - copy ssh config
    - clone the repo
    - wget the auto_update.sh script
    - set up the cron job

## True color RGB LED HAT for Raspberry Pi

![RGB-LED-HAT-size.jpg](./images/RGB-LED-HAT-size.jpg)
![Raspberry-Pi-Zero-Dimensions-Footprint.jpg.webp](./images/Raspberry-Pi-Zero-Dimensions-Footprint.jpg.webp)
### Description
Accessing the RGB LED HAT for Raspberry Pi requires rpi_ws281x library installation:
```bash
pip install rpi_ws281x
```
Find the latest libraries here: https://github.com/jgarff/rpi_ws281x
And the Python bindings here: https://github.com/rpi-ws281x/rpi-ws281x-python

rpi_ws281x introduces a new class called `PixelStrip` which is used to control the strip.
The `PixelStrip` class is initialized with the number of pixels, the GPIO pin to use, and the pixel format.
It defaults to using the GPIO pin 18 and the WS2811 pixel format.
