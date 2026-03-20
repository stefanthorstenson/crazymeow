# Design Specification — Crazypilot

## Document Info

| Field | Value |
|---|---|
| Software | Crazypilot |
| Version | 1.1 |
| Status | Draft — awaiting approval |

---

## Overview

Crazypilot runs on the Raspberry Pi and is responsible for reading Bluetooth controller input and sending velocity setpoint commands to the Crazyflie drone over Crazyradio. It implements a state machine that manages the full flight lifecycle (Standby, Take-off, Flying, Landing, Crazyflie error, Controller error), enforces safety limits, and starts automatically on boot via a systemd service.

---

## Architecture

### Top-level structure

Crazypilot is a single Python process with four concurrent activities running in separate threads:

| Thread | Responsibility |
|---|---|
| Main / State machine | Owns the state machine; runs a fixed-rate loop (~50 Hz); applies safety clamping and sends setpoints |
| Controller input | Polls pygame joystick events; publishes latest axis values to a shared data structure |
| Crazyflie interface | Manages cflib connection lifecycle; receives telemetry via cflib callbacks; exposes latest telemetry |
| Log rotation | Background thread that periodically deletes log files older than 24 hours |

Shared state between threads is protected by `threading.Lock` or `threading.Event` as appropriate. No shared mutable state is accessed without synchronisation.

### Key libraries

| Library | Purpose |
|---|---|
| `cflib` (crazyflie-lib-python) | Crazyflie communication, hover setpoints, telemetry |
| `pygame` (joystick module only) | Gamepad detection and axis reading |
| `logging` + `RotatingFileHandler` | Structured log output to timestamped files |
| `systemd` / `systemctl` | Auto-start (external, configured by setup helpers) |

### Entry point and CLI

```
crazypilot [--controller-mapping <path>]
```

Default mapping path: `~/.config/crazypilot/controller_mapping.json`.

---

## Modules

### `main`

**Purpose:** Entry point. Parses CLI arguments, initialises all subsystems, starts threads, and blocks until shutdown.

**Key responsibilities:**
- Parse `--controller-mapping` flag.
- Instantiate and wire together `ConfigLoader`, `Logger`, `ControllerInput`, `CrazyflieInterface`, and `StateMachine`.
- Start all threads; handle `KeyboardInterrupt` for clean shutdown.

**Public interface:** `main()` — called by the `crazypilot` console script entry point.

---

### `state_machine`

**Purpose:** Core flight logic. Evaluates sensor and controller data on each loop tick and transitions between states. Computes and issues setpoint commands.

**Key responsibilities:**
- Maintain current state (`Standby`, `TakeOff`, `Flying`, `Landing`, `CrazyflieError`, `ControllerError`).
- On each tick: read latest telemetry from `CrazyflieInterface` and latest axis values from `ControllerInput`; apply state logic and send commands via `CrazyflieInterface`.
- Maintain an internal `z_target` (float, metres) representing the current commanded absolute altitude. Updated each tick by integrating the altitude rate command: `z_target += altitude_rate * dt`. Clamped to [0.0, 1.2] m.
- Apply safety clamping (xy speed cap 1.0 m/s, altitude rate cap 0.3 m/s) before issuing any setpoint.
- Apply 5 % deadzone to all joystick axes before use.
- Track timeouts (controller outage 0.5 s, all-zero input 10 s, controller error auto-land 2.0 s, crazyflie outage 0.5 s) using monotonic timestamps.

**State transition summary:**

```
Standby       → TakeOff         : altitude axis > 50 % positive max
TakeOff       → Flying          : altitude > 0.35 m
TakeOff       → CrazyflieError  : CF data gap > 0.5 s
Flying        → Landing         : altitude < 0.2 m  OR  all-zero input > 10 s
Flying        → CrazyflieError  : CF data gap > 0.5 s
Flying        → ControllerError : no controller input > 0.5 s
Landing       → Standby         : landing sequence complete
Landing       → CrazyflieError  : CF data gap > 0.5 s
CrazyflieError→ Standby         : CF data OK
ControllerError→Flying          : controller input received
ControllerError→Landing         : 2.0 s elapsed
ControllerError→CrazyflieError  : CF data gap > 0.5 s
```

**Public interface:**
- `StateMachine(cf_interface, controller_input, config)` — constructor.
- `run()` — blocking loop; call from dedicated thread.
- `stop()` — signals the loop to exit cleanly.

---

### `controller_input`

**Purpose:** Reads joystick axis values from the Bluetooth controller via pygame and makes them available to the state machine.

**Key responsibilities:**
- Initialise `pygame` (joystick module only, headless).
- Continuously poll for `JOYAXISMOTION` events using `pygame.event.get()`.
- Store the latest value for each axis index in a thread-safe structure.
- Record a timestamp of the last event received (used by state machine for controller-outage detection).
- Continuously attempt to detect and reconnect to the configured controller by name if it disappears.

**Public interface:**
- `ControllerInput(controller_name)` — constructor.
- `start()` / `stop()` — manage background polling thread.
- `get_axes() -> dict[int, float]` — returns latest axis values (keyed by axis index).
- `last_event_time() -> float` — monotonic timestamp of last received event.

---

### `crazyflie_interface`

**Purpose:** Manages the cflib connection and exposes telemetry and command methods to the state machine.

**Key responsibilities:**
- Continuously attempt to connect to the Crazyflie at the configured URI using cflib's asynchronous connection API.
- Register cflib log variables for altitude (from Flow Deck) and receive callbacks; store latest values thread-safely.
- Expose methods to send hover setpoints and a stop command.
- Detect data staleness: if no telemetry callback has fired within `crazyflie_outage` (0.5 s), report data as incomplete.
- Reconnect automatically after disconnect without requiring any other component to restart.

**Public interface:**
- `CrazyflieInterface(uri)` — constructor.
- `start()` / `stop()`.
- `is_connected() -> bool`.
- `is_data_ok() -> bool` — False if data gap exceeds 0.5 s.
- `get_altitude() -> float | None`.
- `send_hover_setpoint(vx, vy, yaw_rate, z_target)` — wraps `cf.commander.send_hover_setpoint(vx, vy, yawrate, zdistance)`.
- `send_stop()` — calls `cf.commander.send_stop_setpoint()`.

---

### `joystick_mapper`

**Purpose:** Translates raw pygame axis indices and values into named flight-command values using the loaded controller mapping.

**Key responsibilities:**
- Accept a mapping config dict and a raw axes dict (index → float).
- Apply inversion as specified per axis.
- Apply 5 % deadzone.
- Return a `FlightCommands` named tuple: `altitude_rate`, `yaw_rate`, `velocity_x`, `velocity_y`.

**Public interface:**
- `JoystickMapper(mapping: dict)` — constructor.
- `map(raw_axes: dict[int, float]) -> FlightCommands`.

---

### `config_loader`

**Purpose:** Loads and validates the controller mapping JSON file and the hard-coded Crazyflie URI.

**Key responsibilities:**
- Read and parse `controller_mapping.json` from the path provided at startup.
- Validate that all required keys (`controller_name`, `axes` with the four named axes) are present; raise a descriptive error if not.
- Read the Crazyflie URI from `~/.config/crazypilot/crazypilot_config.json` (written by `configure_crazyflie` during setup).

**Public interface:**
- `load_controller_mapping(path: str) -> dict`.
- `load_crazyflie_uri() -> str` — reads and returns the URI from `crazypilot_config.json`.

---

### `logger`

**Purpose:** Configures application logging and manages log file rotation.

**Key responsibilities:**
- Set up a `logging.Logger` writing to a timestamped file under `~/.local/share/crazypilot/logs/`.
- Also write `WARNING` and above to stderr.
- Start a background daemon thread that scans the log directory every 5 minutes and deletes files with an `mtime` older than 24 hours.

**Public interface:**
- `setup_logging() -> logging.Logger`.
- `start_log_rotation(log_dir: str)` — starts the background rotation thread.

---

## Data Formats

### `controller_mapping.json`

Located at `~/.config/crazypilot/controller_mapping.json` (default).

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

All four axis entries are required. `index` is the pygame axis index (integer). `inverted: true` means the raw value is multiplied by -1 before use.

### Setpoint API

All setpoints are sent via `cf.commander.send_hover_setpoint(vx, vy, yawrate, zdistance)` from cflib. The 4th parameter is **absolute altitude in metres** (not altitude rate). Crazypilot maintains `z_target` internally and passes it as `zdistance` each tick.

| State | Command each tick |
|---|---|
| Standby | none |
| Take-off | `send_hover_setpoint(0, 0, 0, z_target)` — z_target increments at 75 % × 0.3 m/s |
| Flying | `send_hover_setpoint(vx, vy, yaw_rate, z_target)` — z_target integrated from joystick |
| Landing | `send_hover_setpoint(0, 0, 0, z_target)` — z_target decrements at 0.1 m/s; `send_stop()` when z_target ≤ 0.05 m |
| Controller error | `send_hover_setpoint(0, 0, 0, z_target)` — z_target held fixed |
| Crazyflie error | none |

The loop runs at ~50 Hz. The cflib watchdog cuts motors if no setpoint arrives within ~500 ms, which provides a hardware-level safety net.

### `FlightCommands` (internal named tuple)

| Field | Unit | Range (after clamping) |
|---|---|---|
| `altitude_rate` | m/s | ±0.3 |
| `yaw_rate` | °/s | ±45 |
| `velocity_x` | m/s | ±1.0 |
| `velocity_y` | m/s | ±1.0 |

### Log files

Path: `~/.local/share/crazypilot/logs/crazypilot_<YYYYMMDD_HHMMSS>.log`

Format: standard Python `logging` text format with timestamp, level, module, and message. Files older than 24 hours are deleted automatically.

### systemd service file

Installed by the system setup helper. Located at `/etc/systemd/system/crazypilot.service`. Configured with `Restart=always` so the service restarts on crash.

---

## Key Design Decisions

### Thread-per-concern model over asyncio

cflib uses its own internal threads and callback model. pygame's event loop also expects to be pumped from a single thread. Using explicit threads with locks is simpler and more transparent than mixing cflib callbacks with asyncio, and avoids hidden event-loop coupling.

### State machine owns all command output

Only the state machine thread calls `send_hover_setpoint` or `send_land`. No other module sends commands directly. This ensures all safety clamping is applied in one place and the state machine is the single source of truth for what the Crazyflie is doing.

### Crazyflie URI read from config file

The URI is read from `~/.config/crazypilot/crazypilot_config.json` at startup, written there once by `configure_crazyflie` during system setup. It is not changed at runtime.

### Reconnection in CrazyflieInterface, not in StateMachine

The state machine does not know or care whether cflib is actively connected; it only sees `is_data_ok()`. Reconnection logic is encapsulated entirely within `CrazyflieInterface`, keeping the state machine simple.

### `send_hover_setpoint` used exclusively — no high-level commander mixing

The cflib high-level commander (`takeoff`, `land`) is not used. All states use `send_hover_setpoint` with an internal `z_target`, and the landing sequence ends with `send_stop_setpoint()`. This avoids the need to hand off priority between the low-level and high-level commanders (via `send_notify_setpoint_stop`), keeping the control flow simple and predictable.

### Headless pygame initialisation

Only `pygame.joystick` and `pygame.event` are initialised (not the display). This allows Crazypilot to run as a headless systemd service without a display server.
