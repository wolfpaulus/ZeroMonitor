# 🚀 Automation Plan: Auto-Update using Polling

## Launch / Update the app on the Raspberry Pi Zero 2 W

1. Bash script that does all the following:
2. Stops the currently running Python program.
3. Renames the old program directory with a timestamp.
4. Downloads the updated GitHub repo.
5. Creates a new Python virtual environment.
6. Installs the required packages from requirements.txt.
7. Launches the app with access to SPI (specific to Raspberry Pi needs).

### ⚠️ SPI Access Notes (Raspberry Pi)
The script launches the program with sudo because SPI access typically requires root (/dev/spidev0.0).
Make sure the user is in the spi group (sudo usermod -aG spi pi), and SPI is enabled via:
- sudo raspi-config  # Interfacing Options > SPI > Enable
- or - sudo nano /boot/firmware/config.txt  # Add "dtparam=spi=on" to the end of the file

### 🏃 To run the launcher / updater:
```bash
chmod +x update_zero_monitor.sh
./update_zero_monitor.sh
```

## Using cron + git fetch approach to update the app

The script __auto_update_zero_monitor.sh__ runs every 5 minutes via cron and checks if the remote repo has changes in src/

1. Save this as ~/auto_update_zero_monitor.sh
2. Make it executable: ```chmod +x ~/auto_update_zero_monitor.sh```
3. Edit crontab: ```crontab -e```
```
*/5 * * * * /home/<Your Username>/update_zero_monitor.sh >> /home/<Your Username>/zero_monitor.log 2>&1
```

