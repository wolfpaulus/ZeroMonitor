# 🚀 Automation Plan: Auto-Update using Polling

## Launch / Update the app on the Raspberry Pi Zero 2 W

1. Bash script that does all the following:
2. Stops the currently running Python program.
3. Renames the old program directory with a timestamp.
4. Downloads the updated GitHub repo.
5. Creates a new Python virtual environment.
6. Installs the required packages from requirements.txt.
7. Launches the app with access to SPI (specific to Raspberry Pi needs).

### 🏃 To run the launcher / updater:
```bash
chmod +x auto_update_zero_monitor.sh
./auto_update_zero_monitor.sh
```

## Using cron + git fetch approach to update the app

The script __auto_update_zero_monitor.sh__ runs every 5 minutes via cron and checks if the remote repo has changes in src/

1. Save this as ~/auto_update_zero_monitor.sh
2. Make it executable: ```chmod +x ~/auto_update_zero_monitor.sh```
3. Edit crontab: ```crontab -e```
```
*/5 * * * * /home/<Your Username>/auto_update_zero_monitor.sh >> /home/<Your Username>/zero_monitor.log 2>&1
```

