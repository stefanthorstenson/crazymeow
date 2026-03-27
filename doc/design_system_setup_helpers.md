# Design Specification — System Setup Helpers

## Document Info

| Field | Value |
|---|---|
| Software | System Setup Helpers |
| Version | 1.4 |
| Status | Approved |

---

## Overview

System setup helpers is a collection of independent Python scripts for one-time system configuration tasks performed by an experienced developer. The tools cover: writing the Crazyflie radio address over USB, setting the Crazyflie URI in the Crazypilot config, testing the radio connection, installing the Crazypilot systemd service, and enabling SSH on the Raspberry Pi. Each tool is invoked directly and is not part of a unified CLI framework.

---

## Architecture

Each tool is a standalone Python script with a `main()` function and a `if __name__ == "__main__"` guard. Scripts share two utility modules (`sudo_helper` and `git_helper`) that enforce the confirmation requirement before any privileged or cloning operation.

No shared state exists between scripts. Each script is self-contained and exits when its task is complete.

### Directory structure

```
crazymeow/
├── pyproject.toml
├── requirements.txt
├── crazypilot/
│   ├── __init__.py
│   └── <unit>.py
├── controller_setup/
│   ├── __init__.py
│   └── <unit>.py
├── scripts/
│   ├── utils/
│   │   ├── __init__.py
│   │   └── <helper>.py    (one file per utility module described in this document)
│   └── <script>.py        (one file per tool described in this document)
├── doc/
└── README.md
```

Scripts are run directly (`python scripts/<script>.py`) and are not installed as a package. `scripts/utils/` is importable by each script via its package path.

### Key libraries

| Library | Purpose |
|---|---|
| `subprocess` | Running sudo and git commands |
| `cflib` | Crazyflie USB configuration and URI connection test |
| `pathlib` / `json` | Reading and writing config files |

---

## Modules

### `setup_dependencies`

**Purpose:** Installs all Python packages and system packages required by the system.

**Key responsibilities:**
- Use `sudo_helper` to run `apt-get install` for required system packages (`python3-venv`, `python3-pip`, `libusb-1.0-0`).
- Create a Python virtual environment at `<repo_root>/.venv` using the standard `venv` module (skipped if it already exists).
- Install Python packages from `requirements.txt` into the virtual environment using the venv's `pip`.
- Install the crazymeow package itself into the virtual environment using `pip install -e <repo_root>`.
- Print the venv path and the activate command on completion.

---

### `configure_crazyflie`

**Purpose:** Writes the radio address to the Crazyflie over USB and records the resulting URI in `~/.config/crazypilot/crazypilot_config.json` for use by Crazypilot.

**Key responsibilities:**
- Prompt the user to enter the desired radio channel, data rate, and address (or use defaults).
- Connect to the Crazyflie over USB (`usb://0`) in normal firmware mode (no bootloader required).
- Read the current EEPROM configuration via `cf.mem.get_mems(MemoryElement.TYPE_I2C)[0]` and `mem.update(cb)`.
- Write updated values (`radio_channel`, `radio_speed`, `radio_address`, `version=1`) back via `mem.write_data(cb)`. New settings take effect on next power cycle.
- Construct the resulting `radio://` URI and write it to `~/.config/crazypilot/crazypilot_config.json` (creating the file and directory if necessary).
- Print the resulting URI and remind the user to power-cycle the Crazyflie.

**Note:** This script requires the Crazyflie to be connected via USB and running normal firmware.

---

### `test_connection`

**Purpose:** Verifies that the Crazyflie URI stored in the config is reachable over Crazyradio.

**Key responsibilities:**
- Read the URI from `~/.config/crazypilot/crazypilot_config.json`.
- Attempt a cflib connection to the URI with a short timeout.
- Print a clear pass or fail message with the URI that was tested.
- Exit with a non-zero exit code on failure so the script can be used in a shell pipeline or manual verification sequence.

---

### `setup_services`

**Purpose:** Installs and enables the systemd service that auto-starts Crazypilot on boot.

**Key responsibilities:**
- Write a `crazypilot.service` unit file (with `Restart=always`, correct `ExecStart` path, and `User=` set to the current user) to a temporary location.
- Use `sudo_helper` to copy the unit file to `/etc/systemd/system/` with a description printed before execution.
- Use `sudo_helper` to run `systemctl daemon-reload` and `systemctl enable crazypilot`.
- Print confirmation that the service is enabled.

---

### `setup_ssh`

**Purpose:** Enables the SSH server on the Raspberry Pi so the developer can connect remotely.

**Key responsibilities:**
- Use `sudo_helper` to run `systemctl enable ssh` and `systemctl start ssh`.
- Print the Pi's IP address(es) after enabling, so the user knows where to connect.

---

### `sudo_helper`

**Purpose:** Utility module that enforces the requirement (SS-003) that every `sudo` call is preceded by a printed description and user confirmation.

**Key responsibilities:**
- Accept a list of command arguments (the full command including `sudo`) and a human-readable description string.
- Print the description and the exact command that will be run.
- Prompt the user for confirmation (`[y/N]`); abort if not confirmed.
- Execute the command via `subprocess.run`; raise an exception if the command fails.

**Public interface:**
- `run_sudo(cmd: list[str], description: str)` — prints description, prompts, then runs.

---

### `git_helper`

**Purpose:** Utility module that enforces the requirement (SS-004) that every `git clone` is preceded by printed information and user confirmation.

**Key responsibilities:**
- Accept a repository URL, a target directory, and an optional description string.
- Print the repository URL, target directory, and description.
- Prompt the user for confirmation (`[y/N]`); abort if not confirmed.
- Execute `git clone <url> <target>` via `subprocess.run`; raise an exception on failure.

**Public interface:**
- `clone(url: str, target: str, description: str = "")` — prints info, prompts, then clones.

---

## Data Formats

### `crazypilot_config.json`

Located at `~/.config/crazypilot/crazypilot_config.json`. Written by `configure_crazyflie`, read by `test_connection`.

This file contains the radio URI.

```json
{
  "crazyflie_uri": "radio://0/80/2M/E7E7E7E7E7"
}
```

### `crazypilot.service` (generated)

A standard systemd unit file generated in memory and written to `/etc/systemd/system/crazypilot.service` via `sudo_helper`. Key fields:

```ini
[Unit]
Description=Crazypilot drone controller
After=bluetooth.target

[Service]
ExecStart=<repo_root>/.venv/bin/crazypilot
Restart=always
User=<current user>

[Install]
WantedBy=multi-user.target
```

---

## Key Design Decisions

### Independent scripts rather than a unified CLI

The setup tools are used infrequently, in a fixed order, by a developer who understands what each step does. A unified CLI framework would add complexity without benefit. Independent scripts are easier to run selectively and easier to understand and modify.

### `sudo_helper` and `git_helper` as shared utility modules

Centralising the confirmation logic in two utility modules ensures the requirement is enforced consistently across all scripts without duplicating the prompt-and-run pattern. Any future script that needs `sudo` or `git clone` automatically inherits the required behaviour by using these modules.

### `configure_crazyflie` uses cflib directly, not the Crazyflie client

The Crazyflie client is a GUI application and not appropriate as a dependency for a headless script. cflib exposes the same USB configuration API that the client uses internally, and is already a project dependency.
