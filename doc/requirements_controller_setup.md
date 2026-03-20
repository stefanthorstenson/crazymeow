# Requirements Specification — Controller Mapping Setup CLI

## Document Info

| Field | Value |
|---|---|
| Software | Controller Mapping Setup CLI |
| Version | 1.0 |
| Status | Draft — awaiting approval |

---

## 1. Overview

The controller mapping setup CLI is a command-line tool for interactively configuring the Bluetooth controller and mapping its axes to the Crazyflie flight commands used by Crazypilot.

---

## 2. Requirements

### 2.1 General

| ID | Requirement |
|---|---|
| CS-001 | The controller mapping setup shall be implemented as a separate CLI tool, independent of Crazypilot. |
| CS-001b | The CLI shall be invoked with the command `controller-setup`. |
| CS-002 | The CLI shall run on Raspberry Pi with Raspbian OS as its primary target platform. |
| CS-003 | The CLI shall not require super user privileges to run. |
| CS-004 | The CLI shall not download anything from the internet during operation (package installation via pip or apt-get is excluded from this restriction). |
| CS-005 | The code shall be well modularized and easy to maintain. |
| CS-006 | It shall be possible to run the CLI on a laptop with Ubuntu 24.04 and a Crazyradio 2.0 with minimum manual setup. |

### 2.2 Controller Detection

| ID | Requirement |
|---|---|
| CS-010 | The CLI shall detect all connected Bluetooth game controllers and allow the user to select which one to configure. |
| CS-011 | The CLI shall display a human-readable name for each detected controller. |

### 2.3 Axis Mapping

| ID | Requirement |
|---|---|
| CS-020 | The CLI shall guide the user through mapping the following four flight commands, one at a time: altitude rate, yaw rate, forward/backward velocity (x), and left/right velocity (y). |
| CS-021 | For each flight command, the CLI shall instruct the user to move the relevant joystick axis and automatically detect which physical axis was moved. |
| CS-022 | The CLI shall detect and record the correct polarity (inversion) for each axis, based on the direction the user moves the joystick during the mapping procedure. |
| CS-023 | The CLI shall display live axis values during mapping so the user can verify the mapping is correct. |

### 2.4 Configuration Persistence

| ID | Requirement |
|---|---|
| CS-030 | The completed mapping shall be saved to `~/.config/crazypilot/controller_mapping.json`. |
| CS-031 | The configuration file format shall be human-readable (e.g. JSON or YAML). |
| CS-032 | If a configuration file already exists, the CLI shall inform the user and ask for confirmation before overwriting it. |

### 2.5 Verification

| ID | Requirement |
|---|---|
| CS-040 | After all axes have been mapped, the CLI shall present a summary of the mapping and ask the user to confirm before saving. |
| CS-041 | After saving, the CLI shall offer a live test mode where the user can move all joysticks and see the resulting flight command values, to verify the mapping is correct. |
