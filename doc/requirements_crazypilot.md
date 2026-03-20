# Requirements Specification — Crazypilot

## Document Info

| Field | Value |
|---|---|
| Software | Crazypilot |
| Version | 1.0 |
| Status | Draft — awaiting approval |

---

## 1. Overview

Crazypilot is the software running on the Raspberry Pi that reads controller input and sends setpoint commands to the Crazyflie drone.

---

## 2. Requirements

### 2.1 General

| ID | Requirement |
|---|---|
| CP-001 | Crazypilot shall be invoked with the command `crazypilot`. |
| CP-001a | Crazypilot shall run on Raspberry Pi with Raspbian OS as its primary target platform. |
| CP-001b | Crazypilot shall be implemented in Python. |
| CP-002 | Crazypilot shall use crazyflie-lib-python for all flight control communication. |
| CP-003 | The URI of the Crazyflie shall be hard-coded in the software. |
| CP-004 | Crazypilot shall not require super user privileges to run. |
| CP-005 | Crazypilot shall not download anything from the internet during operation (package installation via pip or apt-get is excluded from this restriction). |
| CP-006 | The code shall be well modularized and easy to maintain. |
| CP-007 | It shall be possible to run Crazypilot on a laptop with Ubuntu 24.04 and a Crazyradio 2.0 with minimum manual setup. |

### 2.2 Startup and Connection

| ID | Requirement |
|---|---|
| CP-010 | Crazypilot shall start automatically when the Raspberry Pi boots, without any manual intervention. |
| CP-011 | Crazypilot shall continuously attempt to connect to the Crazyflie (using the hard-coded URI) until a connection is established. |
| CP-012 | Crazypilot shall continuously attempt to connect to the Bluetooth controller until a connection is established. |
| CP-013 | Crazypilot shall be able to connect to the Crazyflie and the Bluetooth controller in any order relative to when Crazypilot starts. |
| CP-014 | Crazypilot shall resume normal operation if the Crazyflie is rebooted, without requiring any other hardware or software to be restarted. |

### 2.3 Flight Control

| ID | Requirement |
|---|---|
| CP-020 | Crazypilot shall control the Crazyflie using hover-assist mode (velocity setpoints), equivalent to the hover mode in the Crazyflie PC client. |
| CP-021 | The left joystick up/down axis shall control the altitude rate. The mapping shall be linear with a 5 % deadzone, and a maximum of ±0.3 m/s. |
| CP-022 | The left joystick left/right axis shall control the yaw rate. The mapping shall be linear with a 5 % deadzone, and a maximum of ±45 °/s. |
| CP-023 | The right joystick up/down axis shall control the velocity in the x-direction of the Crazyflie body frame. Pushing up shall produce positive x velocity (Crazyflie moves forward). The mapping shall be linear with a 5 % deadzone, and a maximum of ±1.0 m/s. |
| CP-024 | The right joystick left/right axis shall control the velocity in the y-direction of the Crazyflie body frame. Pushing right shall move the Crazyflie to its right when the Crazyflie is facing away from the pilot (x-axis pointing away from the pilot). The mapping shall be linear with a 5 % deadzone, and a maximum of ±1.0 m/s. |
| CP-025 | The controller mapping (axis indices and inversion) shall be read from `~/.config/crazypilot/controller_mapping.json` by default, with an optional `--controller-mapping <path>` flag to specify an alternative file path. |

### 2.4 Safety Restrictions

| ID | Requirement |
|---|---|
| CP-030 | Crazypilot shall clamp all altitude rate setpoints so that the Crazyflie cannot exceed an altitude of 1.2 m. |
| CP-031 | Crazypilot shall clamp all velocity setpoints in the xy-plane to a maximum magnitude of 1.0 m/s. |

### 2.5 Error Handling — Controller Input Loss

| ID | Requirement |
|---|---|
| CP-040 | Crazypilot shall detect when controller input has not been received for 0.5 s. |
| CP-041 | When controller input has been absent for 0.5 s, Crazypilot shall command the Crazyflie to hold its current altitude with zero horizontal velocity. |
| CP-042 | Crazypilot shall detect when controller input has not been received for 2.0 s. |
| CP-043 | When controller input has been absent for 2.0 s, Crazypilot shall command the Crazyflie to descend at 0.1 m/s until the altitude is 0.15 m or below. |
| CP-044 | Once the altitude is at or below 0.15 m after the 2.0 s outage, Crazypilot shall send a landing command if one is available in the crazyflie-lib-python API, otherwise it shall stop sending setpoint commands. |

### 2.6 Logging

| ID | Requirement |
|---|---|
| CP-053 | If log files are created, any log file older than 24 hours shall be automatically deleted. |
