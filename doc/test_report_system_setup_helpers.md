# Test Report — System Setup Helpers

## Document Info
| Field | Value |
|---|---|
| Software | System Setup Helpers |
| Requirements version | 1.4 |
| Status | Final |

## Results

| Requirement ID | Description (brief) | Result |
|---|---|---|
| SS-001 | Runs on Raspberry Pi with Raspbian OS | Cannot be tested |
| SS-002 | Code is well modularized | Pass |
| SS-003 | Before each sudo call, prints description and waits for user confirmation | Pass |
| SS-004 | Before each `git clone`, informs user of repo and prompts for confirmation | Pass |
| SS-010 | Tool to write radio address to Crazyflie over USB | Cannot be tested |
| SS-011 | Tool to configure Crazyflie URI, stored in `~/.config/crazypilot/crazypilot_config.json` | Pass |
| SS-012 | Tool to verify configured Crazyflie URI is reachable | Cannot be tested |
| SS-015 | Tool to install all software dependencies | Pass |
| SS-020 | Tool to set up all services necessary for auto-starting Crazypilot on boot | Pass |
| SS-030 | Tool to enable SSH access on the Raspberry Pi | Pass |

## Coverage
- Total requirements: 10
- Pass: 7
- Fail: 0
- Cannot be tested: 3
- Coverage (Pass / (Pass + Fail)): 100%
