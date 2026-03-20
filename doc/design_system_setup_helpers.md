# Design Specification — System Setup Helpers

## Document Info

| Field | Value |
|---|---|
| Software | System Setup Helpers |
| Version | 1.1 |
| Status | Approved |

---

## Overview

System setup helpers is a collection of independent Python scripts for one-time system configuration tasks performed by an experienced developer. The tools cover: writing the Crazyflie radio address over USB, setting the Crazyflie URI in the Crazypilot config, testing the radio connection, installing the Crazypilot systemd service, and enabling SSH on the Raspberry Pi. Each tool is invoked directly and is not part of a unified CLI framework.

---

## Architecture

Each tool is a standalone Python script with a `main()` function and a `if __name__ == "__main__"` guard. Scripts share two utility modules (`sudo_helper` and `git_helper`) that enforce the confirmation requirement before any privileged or cloning operation.

```
scripts/
    setup_dependencies.py    # install Python packages and system packages
    configure_crazyflie.py   # write radio address + set URI in config
    test_connection.py       # verify Crazyflie URI is reachable
    setup_services.py        # install systemd service for auto-start
    setup_ssh.py             # enable SSH on Raspberry Pi
utils/
    sudo_helper.py           # confirmed sudo execution
    git_helper.py            # confirmed git clone execution
```

No shared state exists between scripts. Each script is self-contained and exits when its task is complete.

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
- Use `sudo_helper` to run `apt-get install` for any required system packages (e.g. `python3-pygame`).
- Run `pip install` for Python packages (e.g. `cflib`, `pygame`). A `requirements.txt` in the repository root is used as the package list.
- Clone any required external repositories (e.g. Crazyradio firmware) using `git_helper`.
- Print a summary of what was installed when complete.

---

### `configure_crazyflie`

**Purpose:** Writes the radio address to the Crazyflie over USB and records the resulting URI in `~/.config/crazypilot/crazypilot_config.json` for use by Crazypilot.

**Key responsibilities:**
- Prompt the user to enter the desired radio channel and address (or use defaults).
- Use cflib's USB bootloader / configuration API to write the radio address to the connected Crazyflie (equivalent to "Configure 2.x" in the Crazyflie client).
- Construct the resulting `radio://` URI and write it to `~/.config/crazypilot/crazypilot_config.json` (creating the file and directory if necessary).
- Print the resulting URI so the user can verify it.

**Note:** This script requires the Crazyflie to be connected via USB.

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
ExecStart=/usr/local/bin/crazypilot
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
