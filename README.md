# CrazyMeow

A complete software setup for a kids' version of the Crazyflie, designed to run with a Raspberry Pi as offboard computer and a Bluetooth controller. Key focus areas are ease of use and safety.

## Hardware

- Raspberry Pi with Crazyradio 2.0
- Crazyflie 2.1 with Flow Deck v2
- Bluetooth game controller

---

## System Setup Guide

This setup is performed once by an experienced Crazyflie developer. After completing it, the system can be power-cycled without any manual intervention.

### 1. Install Raspberry Pi OS

Flash Raspberry Pi OS (Raspbian) to an SD card using the Raspberry Pi Imager. During setup, configure Wi-Fi and enable SSH so you can connect remotely.

### 2. Clone the repository

SSH into the Raspberry Pi and clone this repository:

```bash
git clone <this-repo-url> ~/crazymeow
cd ~/crazymeow
```

### 3. Install dependencies

```bash
python3 scripts/setup_dependencies.py
```

This installs required system packages, creates a Python virtual environment at `.venv/` inside the repository, and installs all Python dependencies and the crazymeow package into it. Each `sudo` call prompts for confirmation before executing.

### 4. Enable SSH (if not done during OS setup)

```bash
python scripts/setup_ssh.py
```

This enables and starts the SSH server, and prints the Pi's IP address.

### 5. Configure the Crazyflie radio address

Connect the Crazyflie to the Raspberry Pi via USB and run:

```bash
python scripts/configure_crazyflie.py
```

Enter the desired radio channel, data rate, and address (or press Enter to accept defaults). The script writes the settings to the Crazyflie's EEPROM and saves the resulting URI to `~/.config/crazypilot/crazypilot_config.json`.

**Power-cycle the Crazyflie after this step** for the new radio settings to take effect.

### 6. Verify the radio connection

With the Crazyflie powered on and the Crazyradio plugged in, run:

```bash
python scripts/test_connection.py
```

A clear pass or fail message is printed. Repeat steps 5–6 if the connection fails.

### 7. Pair the Bluetooth controller

Put the controller into pairing mode and pair it using the Raspberry Pi's Bluetooth settings:

```bash
bluetoothctl
# Inside bluetoothctl:
power on
scan on
# Wait for your controller to appear, note its MAC address
pair <MAC>
trust <MAC>
connect <MAC>
quit
```

The controller will reconnect automatically on future boots once trusted.

### 8. Set up the controller mapping

With the Bluetooth controller connected, run the interactive mapping wizard:

```bash
controller-setup
```

The wizard guides you through selecting the controller and moving each joystick axis in turn. The completed mapping is saved to `~/.config/crazypilot/controller_mapping.json`. After saving, a live test mode is offered to verify the mapping.

### 9. Install the crazypilot service

```bash
python scripts/setup_services.py
```

This installs and enables a systemd service that starts crazypilot automatically on every boot. After this step, reboot the Raspberry Pi to confirm the service starts correctly:

```bash
sudo reboot
```

---

## Testing on a Laptop

Crazypilot and the controller mapping setup can be run on a laptop with Ubuntu 24.04 and a Crazyradio 2.0 without the full Raspberry Pi setup.

### Prerequisites

- Python 3.10 or later
- Crazyradio 2.0 plugged in
- Bluetooth controller paired to the laptop

### Install

```bash
git clone <this-repo-url> ~/crazymeow
cd ~/crazymeow
python3 scripts/setup_dependencies.py
```

This creates `.venv/` and installs all dependencies into it. Activate it before running any commands:

```bash
source .venv/bin/activate
```

### Configure

Run steps 5–8 from the system setup guide above (with the venv active). The setup scripts and `controller-setup` command work the same on Ubuntu 24.04.

### Run crazypilot

```bash
crazypilot
```

Or with a custom controller mapping file:

```bash
crazypilot --controller-mapping /path/to/controller_mapping.json
```

---

## How to Start Flying

1. Power on the Crazyflie and place it on a flat surface.
2. Power on the Bluetooth controller.
3. Power on the Raspberry Pi.

The system will connect automatically. Once the Crazyflie telemetry is received and the controller is connected, the system enters **Standby**.

To take off: push the left joystick (altitude) above 50% upward. The Crazyflie will climb to 0.4 m automatically.

Once airborne, use the joysticks to fly:

| Joystick | Direction | Action |
|---|---|---|
| Left | Up / Down | Altitude rate |
| Left | Left / Right | Yaw (rotate) |
| Right | Up / Down | Forward / backward speed |
| Right | Left / Right | Left / right speed |

The Crazyflie will land automatically if:
- It descends below 0.2 m
- All joystick input is zero for more than 10 seconds
- The battery voltage drops below 3.35 V
- The controller signal is lost for more than 2 seconds

---

## Debug Guide

### Connecting via SSH

```bash
ssh pi@<raspberry-pi-ip>
```

The IP address was printed during `setup_ssh.py`. It can also be found with `hostname -I` on the Pi.

### Log files

Crazypilot writes timestamped log files to:

```
~/.local/share/crazypilot/logs/crazypilot_<YYYYMMDD_HHMMSS>.log
```

Log files older than 24 hours are deleted automatically.

To follow the current log in real time:

```bash
tail -f ~/.local/share/crazypilot/logs/$(ls -t ~/.local/share/crazypilot/logs/ | head -1)
```

### Service status

```bash
systemctl status crazypilot
journalctl -u crazypilot -f
```

### Restarting the service

```bash
sudo systemctl restart crazypilot
```
