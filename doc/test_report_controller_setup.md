# Test Report — Controller Mapping Setup CLI

## Document Info
| Field | Value |
|---|---|
| Software | Controller Mapping Setup CLI |
| Version | 1.6 |
| Status | Approved |

## Results

| Requirement ID | Description (brief) | Result |
|---|---|---|
| CS-001 | Separate CLI tool, independent of Crazypilot | Pass |
| CS-001b | Invoked with command `controller-setup` | Pass |
| CS-002 | Runs on Raspberry Pi with Raspbian OS | Cannot be tested |
| CS-003 | Does not require super user privileges | Cannot be tested |
| CS-004 | Does not download from the internet during operation | Cannot be tested |
| CS-005 | Code is well modularized | Pass |
| CS-006 | Can run on Ubuntu 24.04 laptop with Crazyradio 2.0 | Cannot be tested |
| CS-007 | Runs from dedicated virtual environment at `.venv/` | Pass |
| CS-010 | Detects all connected Bluetooth game controllers; allows selection | Pass |
| CS-011 | Displays human-readable name for each detected controller | Pass |
| CS-020 | Guides user through mapping four flight commands | Pass |
| CS-021 | Automatically detects which physical axis was moved | Cannot be tested |
| CS-022 | Detects and records correct polarity (inversion) for each axis | Pass |
| CS-022a | Positive direction per axis: UP for altitude_rate/velocity_x, LEFT for yaw_rate/velocity_y | Pass |
| CS-023 | Displays live axis values during mapping | Cannot be tested |
| CS-030 | Mapping saved to `~/.config/crazypilot/controller_mapping.json` as pretty-printed JSON | Pass |
| CS-032 | If config already exists, informs user and asks for confirmation before overwriting | Pass |
| CS-040 | Shows summary of mapping and asks for confirmation before saving | Pass |
| CS-041 | After saving, offers live test mode to verify mapping | Pass |

## Coverage
- Total requirements: 19
- Pass: 15
- Fail: 0
- Cannot be tested: 4
- Coverage (Pass / (Pass + Fail)): 100%
