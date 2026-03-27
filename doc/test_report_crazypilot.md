# Test Report — Crazypilot

## Document Info
| Field | Value |
|---|---|
| Software | Crazypilot |
| Version | 1.4 |
| Status | Approved |

## Results

| Requirement ID | Description (brief) | Result |
|---|---|---|
| CP-001 | Invoked with command `crazypilot` | Cannot be tested |
| CP-001a | Runs on Raspberry Pi with Raspbian OS | Cannot be tested |
| CP-001b | Implemented in Python | Pass |
| CP-002 | Uses crazyflie-lib-python for flight control | Cannot be tested |
| CP-003 | Reads Crazyflie URI from `~/.config/crazypilot/crazypilot_config.json` | Pass |
| CP-004 | Does not require super user privileges | Cannot be tested |
| CP-005 | Does not download from the internet during operation | Cannot be tested |
| CP-006 | Code is well modularized | Pass |
| CP-007 | Can run on Ubuntu 24.04 laptop with Crazyradio 2.0 | Cannot be tested |
| CP-010 | Starts automatically on Raspberry Pi boot | Cannot be tested |
| CP-011 | Continuously attempts to connect to Crazyflie | Cannot be tested |
| CP-012 | Continuously attempts to connect to Bluetooth controller | Cannot be tested |
| CP-013 | Can connect to Crazyflie and controller in any order | Cannot be tested |
| CP-014 | Resumes normal operation after Crazyflie reboot | Cannot be tested |
| CP-020 | In Flying, uses hover-assist mode (velocity setpoints) | Cannot be tested |
| CP-021 | Left stick up/down -> altitude rate, 5% deadzone, max ±0.3 m/s | Pass |
| CP-022 | Left stick left/right -> yaw rate, 5% deadzone, max ±45 deg/s | Pass |
| CP-023 | Right stick up/down -> velocity x, 5% deadzone, max ±1.0 m/s | Pass |
| CP-024 | Right stick left/right -> velocity y, 5% deadzone, max ±1.0 m/s | Pass |
| CP-025 | Controller mapping read from default path; `--controller-mapping` flag | Pass |
| CP-026 | In Flying, if no controller input, continue sending last command | Pass |
| CP-030 | Altitude rate setpoints clamped so Crazyflie cannot exceed 1.2 m | Pass |
| CP-031 | XY velocity setpoints clamped to maximum magnitude 1.0 m/s | Pass |
| CP-032 | Altitude rate setpoints clamped to maximum magnitude ±0.3 m/s | Pass |
| CP-033 | Altitude > 1.5 m for > 1 s triggers Landing | Pass |
| CP-034 | XY speed > 1.2 m/s for > 1 s triggers Landing | Pass |
| CP-053 | Log files older than 24 hours are automatically deleted | Pass |
| CP-060 | All required system states implemented | Pass |
| CP-061 | Starts in state Initializing | Pass |
| CP-062 | Transitions to Initializing if any part of system rebooted | Cannot be tested |
| CP-063 | In Standby, no commands sent to Crazyflie | Pass |
| CP-064 | In Standby, altitude joystick > 50% and battery > 3.5 V triggers Take-off | Pass |
| CP-065 | In Take-off, no controller input affects the Crazyflie | Pass |
| CP-066 | In Take-off, climb to 0.4 m at 75% of max altitude rate, no xy movement | Pass |
| CP-067 | In Take-off, altitude > 0.35 m triggers Flying | Pass |
| CP-068 | In Take-off, CF data incomplete > 0.5 s triggers Crazyflie error | Pass |
| CP-069 | In Take-off, battery < 3.35 V triggers Landing | Pass |
| CP-070 | In Flying, altitude < 0.2 m triggers Landing | Pass |
| CP-071 | In Flying, all commands zero for > 10 s triggers Landing | Pass |
| CP-072 | In Flying, CF data incomplete triggers Crazyflie error | Pass |
| CP-073 | In Flying, no controller input > 0.5 s triggers Controller error | Pass |
| CP-074 | In Landing, descend at 0.1 m/s until altitude <= 0.05 m | Pass |
| CP-075 | In Landing, stop sending commands once altitude <= 0.05 m | Pass |
| CP-076 | After landing sequence completes, transition to Standby | Pass |
| CP-077 | In Landing, CF data incomplete triggers Crazyflie error | Pass |
| CP-078 | In Crazyflie error, no commands sent | Pass |
| CP-079 | In Crazyflie error, when data ok, transition to Standby | Pass |
| CP-080 | In Controller error, hold current altitude with zero horizontal velocity | Pass |
| CP-081 | In Controller error, if controller input received, transition to Flying | Pass |
| CP-082 | In Controller error, after 2.0 s, transition to Landing | Pass |
| CP-083 | In Controller error, if CF data incomplete, transition to Crazyflie error | Pass |
| CP-084 | In Flying, battery < 3.35 V triggers Landing | Pass |
| CP-085 | In Initializing, no commands sent to Crazyflie | Pass |
| CP-086 | In Initializing, CF data ok and controller connected triggers Standby | Pass |

## Coverage
- Total requirements: 55
- Pass: 38
- Fail: 0
- Cannot be tested: 17
- Coverage (Pass / (Pass + Fail)): 100%
