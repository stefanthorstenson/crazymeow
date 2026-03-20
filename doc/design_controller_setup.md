# Design Specification — Controller Mapping Setup CLI

## Document Info

| Field | Value |
|---|---|
| Software | Controller Mapping Setup CLI |
| Version | 1.1 |
| Status | Approved |

---

## Overview

The controller mapping setup CLI (`controller-setup`) is a standalone interactive command-line wizard that detects connected Bluetooth game controllers, guides the user through mapping the four flight-control axes, and saves the result to `~/.config/crazypilot/controller_mapping.json`. It is independent of Crazypilot and does not need to be run while Crazypilot is active.

---

## Architecture

The tool is a single-threaded Python process that runs sequentially through a fixed wizard flow:

```
Detect controllers → Select controller → Map axes (x4) → Confirm summary → Save → Optional live test → Exit
```

pygame is used for all controller interaction (detection, axis polling). There is no background threading; pygame events are polled synchronously in tight loops during interactive steps.

### Key libraries

| Library | Purpose |
|---|---|
| `pygame` (joystick module) | Controller detection and axis reading |
| `json` | Reading and writing the mapping file |
| `pathlib` | Config directory creation |

---

## Modules

### `main`

**Purpose:** Entry point. Orchestrates the wizard flow by calling the other modules in sequence.

**Key responsibilities:**
- Initialise pygame (headless, joystick module only).
- Call `controller_detector` to enumerate and select a controller.
- Call `axis_mapper` to run the interactive mapping wizard.
- Display the mapping summary and ask for confirmation.
- Call `config_writer` to persist the result.
- Offer the live test and call `live_tester` if accepted.
- Handle errors from each step with user-friendly messages.

**Public interface:** `main()` — called by the `controller-setup` console script entry point.

---

### `controller_detector`

**Purpose:** Enumerates connected joystick/gamepad devices via pygame and lets the user pick one.

**Key responsibilities:**
- Call `pygame.joystick.get_count()` and initialise each joystick.
- Display a numbered list of controller names.
- Prompt the user to enter a number; validate input.
- Return the selected `pygame.joystick.Joystick` instance and its human-readable name.
- If no controllers are found, print a clear message and exit.

**Public interface:**
- `detect_and_select() -> tuple[pygame.joystick.Joystick, str]` — returns `(joystick, name)`.

---

### `axis_mapper`

**Purpose:** Guides the user through mapping each of the four flight commands to a physical axis, one at a time, and determines the correct inversion for each.

**Key responsibilities:**
- Iterate over the four axis roles in order: `altitude_rate`, `yaw_rate`, `velocity_x`, `velocity_y`.
- For each role:
  - Print instructions describing which physical stick to move (e.g., "Push the left stick UP for altitude rate, then release.").
  - Poll pygame events in a loop, showing live axis values for all axes on screen.
  - Detect which axis index has the largest absolute displacement above a threshold (0.3) — that is the selected axis.
  - Record the sign of the displacement at detection time; if the displacement is negative when a positive input is expected, set `inverted: true`.
  - Wait for the axis to return near zero before moving to the next role (to avoid bleed-over detection).
- Return a mapping dict in the `controller_mapping.json` axes schema.

**Inversion logic:** Each axis role has an expected positive direction (e.g., "push up" for `altitude_rate`). The pygame value at detection is compared against the expected direction. If the value is negative, `inverted` is set to `true` so that Crazypilot can always apply a consistent inversion at runtime.

**Public interface:**
- `map_axes(joystick: pygame.joystick.Joystick) -> dict` — returns the `"axes"` sub-dict.

---

### `config_writer`

**Purpose:** Saves the completed mapping to `~/.config/crazypilot/controller_mapping.json`.

**Key responsibilities:**
- Create `~/.config/crazypilot/` if it does not exist.
- If the file already exists, print a warning and ask for confirmation before overwriting (requirement CS-032).
- Write the mapping as pretty-printed JSON (indent=2).

**Public interface:**
- `save(mapping: dict, path: str | None = None)` — `path` defaults to `~/.config/crazypilot/controller_mapping.json`.

---

### `live_tester`

**Purpose:** Provides an interactive live test mode after saving, so the user can verify the mapping produces the expected flight command values.

**Key responsibilities:**
- Load the just-saved mapping (or accept it as a parameter).
- Poll pygame axis events in a loop.
- For each tick, apply the mapping (index lookup + inversion) and display the resulting four flight command values alongside the raw axis values.
- Apply the same 5 % deadzone as Crazypilot uses, so the output matches what Crazypilot will see.
- Exit on a keypress (`q` or `Ctrl+C`).

**Public interface:**
- `run_live_test(joystick: pygame.joystick.Joystick, mapping: dict)`.

---

## Data Formats

### `controller_mapping.json`

Saved to `~/.config/crazypilot/controller_mapping.json`. Pretty-printed with indent=2.

```json
{
  "controller_name": "Xbox Controller",
  "axes": {
    "altitude_rate": {"index": 1, "inverted": false},
    "yaw_rate":      {"index": 0, "inverted": false},
    "velocity_x":    {"index": 3, "inverted": true},
    "velocity_y":    {"index": 2, "inverted": false}
  }
}
```

The four axis roles are fixed. `index` is the pygame axis index. `inverted` is a boolean.

### Wizard interaction (terminal I/O)

All user-facing output goes to stdout. Input is read with `input()`. Live axis displays use `\r` (carriage return) to overwrite the current line in the terminal, avoiding excessive scrolling.

---

## Key Design Decisions

### Single-threaded sequential wizard

The wizard is inherently sequential (one step at a time), so a single-threaded design is natural. pygame event polling in a tight loop is sufficient for responsive axis detection without background threads.

### Axis detection by largest displacement

Detecting the axis with the largest absolute displacement above a threshold is robust against slight drift on other axes and does not require the user to move the stick to a precise position. A threshold of 0.3 (30 % of range) gives a good balance between sensitivity and false-positive rejection.

### Inversion recorded at mapping time, not at runtime

Recording `inverted` in the config file means Crazypilot only needs to apply a simple sign flip; no direction-detection logic is needed at runtime. This also makes the saved file human-readable and easy to hand-edit if needed.

### Live tester applies the same deadzone as Crazypilot

The live tester intentionally replicates Crazypilot's 5 % deadzone so the user sees exactly the values Crazypilot will use. This makes the test meaningful as a verification step rather than just a raw axis display.

### Config directory created on write, not on startup

The `~/.config/crazypilot/` directory is created only when `config_writer.save()` is called. This avoids creating empty directories when the tool exits early (e.g., if no controller is detected).
