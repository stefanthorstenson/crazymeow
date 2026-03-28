# Design Specification — Crazypilot

## Document Info

| Field | Value |
|---|---|
| Software | Crazypilot |
| Version | 1.6 |
| Status | Approved |

---

## Overview

Crazypilot runs on the Raspberry Pi and is responsible for reading Bluetooth controller input and sending velocity setpoint commands to the Crazyflie drone over Crazyradio. It implements a state machine that manages the full flight lifecycle (Initializing, Standby, Take-off, Flying, Landing, Crazyflie error, Controller error), enforces safety limits, and starts automatically on boot via a systemd service.

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

### Coordinate system

The system uses the Crazyflie body frame: X = forward, Y = left, Z = up. All velocity setpoints follow this convention — positive `vy` moves the drone left, positive `vx` moves it forward. Sign correction is handled entirely at mapping time by the controller setup (via the `inverted` flag in `controller_mapping.json`); no inversion is applied in the state machine.

### Key libraries

| Library | Purpose |
|---|---|
| `cflib` (crazyflie-lib-python) | Crazyflie communication, hover setpoints, telemetry |
| `pygame` (joystick module only) | Gamepad detection and axis reading |
| `logging` + `FileHandler` | Structured log output to one timestamped file per invocation, with UTC timestamps |
| `systemd` / `systemctl` | Auto-start (external, configured by setup helpers) |

### Entry point and CLI

```
crazypilot [--controller-mapping <path>] [--debug]
```

Default mapping path: `~/.config/crazypilot/controller_mapping.json`.

### Directory structure

```
crazymeow/
├── pyproject.toml
├── requirements.txt
├── crazypilot/
│   ├── __init__.py
│   └── <unit>.py          (one file per module described in this document)
├── controller_setup/
│   ├── __init__.py
│   └── <unit>.py
├── scripts/
│   ├── utils/
│   │   ├── __init__.py
│   │   └── <helper>.py
│   └── <script>.py
├── doc/
└── README.md
```

`crazypilot` is installed as a Python package via `pyproject.toml`. The `crazypilot` console command maps to `crazypilot.main:main`.

---

## Modules

### `main`

**Purpose:** Entry point. Parses CLI arguments, initialises all subsystems, starts threads, and blocks until shutdown.

**Key responsibilities:**
- Parse `--controller-mapping` and `--debug` flags.
- Call `setup_logging(debug=<flag>)` before anything else.
- Instantiate and wire together `ConfigLoader`, `Logger`, `ControllerInput`, `CrazyflieInterface`, and `StateMachine`.
- Start all threads; handle `KeyboardInterrupt` for clean shutdown.

**Public interface:** `main()` — called by the `crazypilot` console script entry point.

---

### `state_machine`

**Purpose:** Core flight logic. Evaluates sensor and controller data on each loop tick and transitions between states. Computes and issues setpoint commands.

**Key responsibilities:**
- Maintain current state (`Initializing`, `Standby`, `TakeOff`, `Flying`, `Landing`, `CrazyflieError`, `ControllerError`).
- On each tick: read latest telemetry from `CrazyflieInterface` and latest axis values from `ControllerInput`; apply state logic and send commands via `CrazyflieInterface`.
- Maintain an internal `z_target` (float, metres) representing the current commanded absolute altitude. Updated each tick by integrating the altitude rate command: `z_target += altitude_rate * dt`. Clamped to [0.0, 1.2] m.
- Apply safety clamping (xy speed cap 1.0 m/s, altitude rate cap 0.3 m/s) before issuing any setpoint.
- Apply 5 % deadzone to all joystick axes before use.
- Track timeouts (controller outage 0.5 s, all-zero input 10 s, controller error auto-land 2.0 s, crazyflie outage 0.5 s) using monotonic timestamps.
- Monitor reported altitude and xy speed each tick for safety violations: if altitude > 1.5 m or xy speed > 1.2 m/s, start a 1 s violation timer; reset the timer if the condition clears; transition to Landing if the timer expires.
- Monitor battery state (pm.state) each tick: in Standby, only allow transition to TakeOff if pm.state ≠ 3 (not low-power); in TakeOff and Flying, transition to Landing if pm.state == 3 (low-power). Using the firmware's pm.state rather than a raw voltage threshold avoids false triggers from momentary voltage sag during motor spin-up.
- In Standby, send a stop setpoint every 200 ms (tracked via a monotonic timestamp `_last_standby_stop_time`) to keep the Crazyflie firmware watchdog alive. The watchdog fires at 500 ms (warning) and 2000 ms (ExceptFreeFall lock). Without this keepalive the drone cannot re-arm for a second takeoff.
- Emit a periodic log entry at approximately 1 Hz (tracked via a monotonic timestamp, not a separate thread). Each entry contains: current state, altitude, battery voltage, battery state (pm.state), raw altitude axis value, and time since last controller event in milliseconds (or `None` if no event received yet).
- In state Standby, track the rising edge of the altitude axis threshold (50 % positive max): when the axis crosses from below to above the threshold and the takeoff condition is not met, log the blocking reason once (battery too low, or no battery reading). Reset the edge-detect flag when the axis drops back below threshold.
- When transitioning to state Landing, log the reason. The `_transition` method accepts an optional `reason: str` parameter; when the new state is `Landing` and a reason is provided it is appended to the transition log message.

**State transition summary:**

```
Initializing  → Standby         : CF data OK  AND  controller connected  AND  pm.state == 0
Standby       → TakeOff         : altitude axis > 50 % positive max  AND  pm.state ≠ 3
TakeOff       → Flying          : altitude > 0.35 m
TakeOff       → CrazyflieError  : CF data gap > 0.5 s
TakeOff       → Landing         : pm.state == 3
Flying        → Landing         : altitude < 0.2 m  OR  all-zero input > 10 s  OR  altitude > 1.5 m for > 1 s  OR  xy speed > 1.2 m/s for > 1 s  OR  pm.state == 3
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
- Continuously attempt to detect and reconnect to the configured controller by name if it disappears. `JOYDEVICEADDED` events are only processed when `self._joystick is None`; if the controller is already connected the event is ignored. This prevents a feedback loop where calling `pygame.joystick.quit()` / `pygame.joystick.init()` inside `_find_joystick` would itself generate new `JOYDEVICEADDED` events.

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
- In the `connected` callback: create and add a `LogConfig` named `"StateEstimate"` with a 20 ms period (50 Hz), containing the variables `stateEstimate.z`, `stateEstimate.vx`, `stateEstimate.vy`, `pm.vbat`, and `pm.state`. Register a data callback and start the log config.
- In the log data callback: store the latest values of `z`, `vx`, `vy`, and `vbat` in thread-safe attributes; record the timestamp of the last callback for staleness detection.
- In the `disconnected` callback: mark data as stale and stop reconnect attempts until a new connection cycle begins.
- Expose methods to send hover setpoints and a stop command.
- Detect data staleness: if no log callback has fired within `crazyflie_outage` (0.5 s), report data as incomplete.
- Reconnect automatically after disconnect without requiring any other component to restart.

**Public interface:**
- `CrazyflieInterface(uri)` — constructor.
- `start()` / `stop()`.
- `is_connected() -> bool`.
- `is_data_ok() -> bool` — False if data gap exceeds 0.5 s.
- `get_altitude() -> float | None` — latest `stateEstimate.z` value in metres.
- `get_xy_speed() -> float | None` — magnitude of latest (`stateEstimate.vx`, `stateEstimate.vy`) in m/s.
- `get_battery_voltage() -> float | None` — latest `pm.vbat` value in volts.
- `get_battery_state() -> int | None` — latest `pm.state` value (0=battery, 1=charging, 2=charged, 3=low-power, 4=shutdown); `None` if no data received yet.
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
- Accept a `debug: bool` parameter.
- Set up a `logging.Logger` writing to a timestamped log file under `~/.local/share/crazypilot/logs/` using a plain `FileHandler` (one file per invocation; no in-process rotation).
- Use UTC timestamps in all log entries by setting `formatter.converter = time.gmtime`.
- When `debug=True`, add a `StreamHandler(sys.stdout)` at `DEBUG` level so all log output is also printed to stdout.
- Start a background daemon thread that scans the log directory every 5 minutes and deletes files with an `mtime` older than 24 hours (CP-053).

**Public interface:**
- `setup_logging(debug: bool = False) -> logging.Logger`.
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

### Crazyflie log configuration

A single `LogConfig` block is created and started in the `connected` callback. It is stopped and deleted in the `disconnected` callback and recreated on the next connection.

| Field | Value |
|---|---|
| Name | `"StateEstimate"` |
| Period | 20 ms (50 Hz) |

| Variable | Type | Description |
|---|---|---|
| `stateEstimate.z` | `float` | Altitude above take-off surface in metres (Flow Deck v2) |
| `stateEstimate.vx` | `float` | Velocity in Crazyflie body x-direction in m/s |
| `stateEstimate.vy` | `float` | Velocity in Crazyflie body y-direction in m/s |
| `pm.vbat` | `float` | Battery voltage in volts |
| `pm.state` | `int8_t` | Power management state: 0=battery, 1=charging, 2=charged, 3=low-power, 4=shutdown |

The callback stores all values atomically under a `threading.Lock`. The `is_data_ok()` staleness check is driven by the timestamp of the last successful callback, not by the connection status alone — this ensures a connected-but-silent Crazyflie is still treated as an error.

### Setpoint API

All setpoints are sent via `cf.commander.send_hover_setpoint(vx, vy, yawrate, zdistance)` from cflib. The 4th parameter is **absolute altitude in metres** (not altitude rate). Crazypilot maintains `z_target` internally and passes it as `zdistance` each tick.

| State | Command each tick |
|---|---|
| Standby | `send_stop()` every 200 ms (watchdog keepalive only) |
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

The timestamp in the filename is UTC. One file is created per invocation; there is no in-process rotation. Format: standard Python `logging` text format — `%(asctime)s %(levelname)s %(module)s %(message)s` — with UTC timestamps. Files older than 24 hours are deleted automatically.

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
