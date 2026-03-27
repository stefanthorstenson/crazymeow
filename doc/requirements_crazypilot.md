# Requirements Specification — Crazypilot

## Document Info

| Field | Value |
|---|---|
| Software | Crazypilot |
| Version | 1.5 |
| Status | Approved |

---

## Overview

Crazypilot is the software running on the Raspberry Pi that reads controller input and sends setpoint commands to the Crazyflie drone.

---

## Requirements

### General

| ID | Requirement |
|---|---|
| CP-001 | Crazypilot shall be invoked with the command `crazypilot`. |
| CP-001a | Crazypilot shall run on Raspberry Pi with Raspbian OS as its primary target platform. |
| CP-001b | Crazypilot shall be implemented in Python. |
| CP-002 | Crazypilot shall use crazyflie-lib-python for all flight control communication. |
| CP-003 | Crazypilot shall read the Crazyflie URI from `~/.config/crazypilot/crazypilot_config.json`. Info: The URI is set once during manual setup and not changed at runtime. |
| CP-004 | Crazypilot shall not require super user privileges to run. |
| CP-005 | Crazypilot shall not download anything from the internet during operation (package installation via pip or apt-get is excluded from this restriction). |
| CP-006 | The code shall be well modularized and easy to maintain. |
| CP-007 | It shall be possible to run Crazypilot on a laptop with Ubuntu 24.04 and a Crazyradio 2.0 with minimum manual setup. |
| CP-008 | Crazypilot shall run from the dedicated Python virtual environment located at `.venv/` in the repository root. |

### Startup and Connection

| ID | Requirement |
|---|---|
| CP-010 | Crazypilot shall start automatically when the Raspberry Pi boots, without any manual intervention. |
| CP-011 | Crazypilot shall continuously attempt to connect to the Crazyflie until a connection is established. |
| CP-012 | Crazypilot shall continuously attempt to connect to the Bluetooth controller until a connection is established. |
| CP-013 | Crazypilot shall be able to connect to the Crazyflie and the Bluetooth controller in any order relative to when Crazypilot starts. |
| CP-014 | Crazypilot shall resume normal operation if the Crazyflie is rebooted, without requiring any other hardware or software to be restarted. |

### Controller Mapping

| ID | Requirement |
|---|---|
| CP-025 | The controller mapping (axis indices and inversion) shall be read from `~/.config/crazypilot/controller_mapping.json` by default, with an optional `--controller-mapping <path>` flag to specify an alternative file path. |

### Safety

| ID | Requirement |
|---|---|
| CP-030 | Crazypilot shall clamp all altitude rate setpoints so that the Crazyflie cannot exceed an altitude of 1.2 m. |
| CP-031 | Crazypilot shall clamp all velocity setpoints in the xy-plane to a maximum magnitude of 1.0 m/s. |
| CP-032 | Crazypilot shall clamp all altitude rate setpoints to a maximum magnitude of 0.3 m/s. |
| CP-033 | If the Crazyflie's reported altitude exceeds 1.5 m (maximum_altitude + 0.3 m) for more than 1 second, Crazypilot shall transition to state Landing. |
| CP-034 | If the Crazyflie's reported speed in the xy plane exceeds 1.2 m/s (maximum_speed_in_xy_plane + 0.2 m/s) for more than 1 second, Crazypilot shall transition to state Landing. |

### System States

| ID | Requirement |
|---|---|
| CP-060 | Crazypilot shall implement the following system states: Initializing, Standby, Take-off, Flying, Landing, Crazyflie error, Controller error. |
| CP-061 | Crazypilot shall start in state Initializing. |
| CP-062 | If any part of the system is rebooted, Crazypilot shall transition to state Initializing. |

#### State Initializing

| ID | Requirement |
|---|---|
| CP-085 | In state Initializing, Crazypilot shall not send any commands to the Crazyflie. |
| CP-086 | In state Initializing, when Crazyflie telemetry is being received, the Bluetooth controller is connected, and the battery state is 0 (normal), Crazypilot shall transition to state Standby. |

#### State Standby

| ID | Requirement |
|---|---|
| CP-063 | In state Standby, Crazypilot shall not send any flight commands to the Crazyflie. |
| CP-063b | In state Standby, Crazypilot shall send a stop setpoint every 200 ms to prevent the Crazyflie firmware watchdog from expiring. |
| CP-064 | In state Standby, when the altitude joystick input exceeds 50 % of its positive maximum and the Crazyflie battery is not in low-power state (pm.state ≠ 3), Crazypilot shall transition to state Take-off. |

#### State Take-off

| ID | Requirement |
|---|---|
| CP-065 | In state Take-off, no controller input shall affect the Crazyflie. |
| CP-066 | In state Take-off, Crazypilot shall command the Crazyflie to reach an altitude of 0.4 m at 75 % of the maximum allowed altitude rate, with no movement in the xy-plane. |
| CP-067 | In state Take-off, when the Crazyflie altitude exceeds 0.35 m, Crazypilot shall transition to state Flying. |
| CP-068 | In state Take-off, if Crazyflie data is incomplete for more than crazyflie_outage (0.5 s), Crazypilot shall transition to state Crazyflie error. |
| CP-069 | In state Take-off, if the Crazyflie battery is in low-power state (pm.state = 3), Crazypilot shall transition to state Landing. |

#### State Flying

| ID | Requirement |
|---|---|
| CP-020 | In state Flying, Crazypilot shall control the Crazyflie using hover-assist mode (velocity setpoints), equivalent to the hover mode in the Crazyflie PC client. |
| CP-021 | The left joystick up/down axis shall control the altitude rate. The mapping shall be linear with a 5 % deadzone, and a maximum of ±0.3 m/s. |
| CP-022 | The left joystick left/right axis shall control the yaw rate. The mapping shall be linear with a 5 % deadzone, and a maximum of ±45 °/s. |
| CP-023 | The right joystick up/down axis shall control the velocity in the x-direction of the Crazyflie body frame. Pushing up shall produce positive x velocity (Crazyflie moves forward). The mapping shall be linear with a 5 % deadzone, and a maximum of ±1.0 m/s. |
| CP-024 | The right joystick left/right axis shall control the velocity in the y-direction of the Crazyflie body frame. Pushing right shall move the Crazyflie to its right when the Crazyflie is facing away from the pilot (x-axis pointing away from the pilot). The mapping shall be linear with a 5 % deadzone, and a maximum of ±1.0 m/s. |
| CP-026 | In state Flying, if controller input is absent, Crazypilot shall continue sending the last received command to the Crazyflie. |
| CP-070 | In state Flying, when the Crazyflie altitude drops below 0.2 m, Crazypilot shall transition to state Landing. |
| CP-071 | In state Flying, if all controller input is zero for more than 10 s, Crazypilot shall transition to state Landing. |
| CP-072 | In state Flying, if Crazyflie data is incomplete for more than crazyflie_outage (0.5 s), Crazypilot shall transition to state Crazyflie error. |
| CP-073 | In state Flying, if no controller input is received for more than 0.5 s, Crazypilot shall transition to state Controller error. |
| CP-084 | In state Flying, if the Crazyflie battery is in low-power state (pm.state ≠ 3),  Crazypilot shall transition to state Landing. |

#### State Landing

| ID | Requirement |
|---|---|
| CP-074 | In state Landing, Crazypilot shall command the Crazyflie to descend at 0.1 m/s until the altitude is at or below 0.05 m. |
| CP-075 | Once altitude is at or below 0.05 m in state Landing, Crazypilot shall stop sending commands. |
| CP-076 | After the landing sequence completes, Crazypilot shall transition to state Standby. |
| CP-077 | In state Landing, if Crazyflie data is incomplete for more than crazyflie_outage (0.5 s), Crazypilot shall transition to state Crazyflie error. |

#### State Crazyflie error

| ID | Requirement |
|---|---|
| CP-078 | In state Crazyflie error, Crazypilot shall not send any commands to the Crazyflie. |
| CP-079 | In state Crazyflie error, when Crazyflie data is received and is complete, Crazypilot shall transition to state Standby. |

#### State Controller error

| ID | Requirement |
|---|---|
| CP-080 | In state Controller error, Crazypilot shall command the Crazyflie to hold its current altitude with zero horizontal velocity. |
| CP-081 | In state Controller error, if controller input is received, Crazypilot shall transition to state Flying. |
| CP-082 | In state Controller error, after 2.0 s, Crazypilot shall transition to state Landing. |
| CP-083 | In state Controller error, if Crazyflie data is incomplete for more than crazyflie_outage (0.5 s), Crazypilot shall transition to state Crazyflie error. |

### Logging

| ID | Requirement |
|---|---|
| CP-053 | Any log file older than 24 hours shall be automatically deleted. |
| CP-054 | Crazypilot shall create one log file per invocation, named with a UTC timestamp, stored in `~/.local/share/crazypilot/logs/`. |
| CP-055 | All log entries shall use UTC timestamps. |
| CP-056 | Crazypilot shall write a periodic log entry approximately once per second containing: current state, altitude, battery voltage, battery state (pm.state), raw altitude axis value, and time since last controller event in milliseconds. |
| CP-057 | When in state Standby, if the altitude axis input crosses above the takeoff threshold (50 % of positive maximum) and the takeoff condition is not met, Crazypilot shall log the reason. This shall be logged once per rising edge of the threshold (not continuously). |
| CP-058 | When Crazypilot transitions to state Landing, it shall log the reason for the transition. |
| CP-059 | Crazypilot shall support a `--debug` flag. In debug mode, all log output shall also be written to stdout. |
