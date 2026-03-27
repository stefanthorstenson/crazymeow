import time
import math
import logging
from enum import Enum, auto

logger = logging.getLogger("crazypilot")

_LOOP_HZ = 50
_LOOP_DT = 1.0 / _LOOP_HZ

_CF_OUTAGE_TIMEOUT = 0.5       # seconds
_CONTROLLER_OUTAGE_TIMEOUT = 0.5
_ALL_ZERO_TIMEOUT = 10.0
_CONTROLLER_ERROR_LAND_TIMEOUT = 2.0

_PM_STATE_LOW_POWER = 3

_TAKEOFF_ALT_THRESHOLD = 0.35  # m — transition TakeOff → Flying
_LANDING_ALT_THRESHOLD = 0.2   # m — trigger Landing from Flying
_LANDING_STOP_ALT = 0.05       # m — stop motors in Landing

_TAKEOFF_RATE_FACTOR = 0.75
_MAX_ALTITUDE_RATE = 0.3       # m/s
_TAKEOFF_RATE = _TAKEOFF_RATE_FACTOR * _MAX_ALTITUDE_RATE  # 0.225 m/s
_LANDING_RATE = 0.1            # m/s (descent)

_Z_TARGET_MIN = 0.0
_Z_TARGET_MAX = 1.2            # m

_MAX_XY_SPEED = 1.0            # m/s (setpoint clamp)
_SAFETY_ALT_LIMIT = 1.5        # m
_SAFETY_XY_SPEED_LIMIT = 1.2   # m/s
_SAFETY_VIOLATION_DURATION = 1.0  # seconds

_TAKEOFF_TARGET_ALT = 0.4      # m

_ALTITUDE_AXIS_TAKEOFF_THRESHOLD = 0.5  # raw value > 50% positive


class State(Enum):
    Initializing = auto()
    Standby = auto()
    TakeOff = auto()
    Flying = auto()
    Landing = auto()
    CrazyflieError = auto()
    ControllerError = auto()


class StateMachine:
    def __init__(self, cf_interface, controller_input, joystick_mapper, config):
        self._cf = cf_interface
        self._ctrl = controller_input
        self._mapper = joystick_mapper
        self._config = config

        self._state = State.Initializing
        self._running = False
        self._z_target = 0.0

        self._safety_violation_start = None
        self._all_zero_start = None
        self._controller_error_start = None
        self._last_periodic_log_time = None
        self._alt_above_threshold_prev = False

    def run(self):
        self._running = True
        logger.info("State machine started, state=Initializing")

        while self._running:
            t_start = time.monotonic()
            self._tick()
            elapsed = time.monotonic() - t_start
            sleep_time = _LOOP_DT - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def stop(self):
        self._running = False

    def _tick(self):
        state = self._state
        raw_axes = self._ctrl.get_axes()
        last_event = self._ctrl.last_event_time()
        data_ok = self._cf.is_data_ok()
        altitude = self._cf.get_altitude()
        xy_speed = self._cf.get_xy_speed()
        battery = self._cf.get_battery_voltage()
        pm_state = self._cf.get_battery_state()
        now = time.monotonic()

        self._emit_periodic_log(raw_axes, altitude, battery, pm_state, last_event, now)

        if state == State.Initializing:
            self._handle_initializing(data_ok, last_event, now)

        elif state == State.Standby:
            self._handle_standby(raw_axes, pm_state)

        elif state == State.TakeOff:
            self._handle_takeoff(data_ok, altitude, pm_state)

        elif state == State.Flying:
            self._handle_flying(raw_axes, last_event, data_ok, altitude, xy_speed, pm_state, now)

        elif state == State.Landing:
            self._handle_landing(data_ok)

        elif state == State.CrazyflieError:
            self._handle_cf_error(data_ok)

        elif state == State.ControllerError:
            self._handle_controller_error(last_event, data_ok, now)

    def _transition(self, new_state: State, reason: str = None):
        if new_state == State.Landing and reason:
            logger.info("State: %s → %s (%s)", self._state.name, new_state.name, reason)
        else:
            logger.info("State: %s → %s", self._state.name, new_state.name)
        self._state = new_state

    # -------------------------------------------------------------------------
    # Periodic logging
    # -------------------------------------------------------------------------

    def _emit_periodic_log(self, raw_axes, altitude, battery, pm_state, last_event, now):
        if self._last_periodic_log_time is None or (now - self._last_periodic_log_time) >= 1.0:
            self._last_periodic_log_time = now
            raw_alt = self._mapper.get_raw_altitude_input(raw_axes)
            ctrl_age_ms = round((now - last_event) * 1000) if last_event is not None else None
            logger.info(
                "STATUS state=%s alt=%s bat=%s pm_state=%s raw_alt=%s ctrl_age_ms=%s",
                self._state.name,
                f"{altitude:.3f}" if altitude is not None else "None",
                f"{battery:.2f}" if battery is not None else "None",
                pm_state,
                f"{raw_alt:.3f}",
                ctrl_age_ms,
            )

    # -------------------------------------------------------------------------
    # State handlers
    # -------------------------------------------------------------------------

    def _handle_initializing(self, data_ok, last_event, now):
        controller_connected = (
            last_event is not None and (now - last_event) <= _CONTROLLER_OUTAGE_TIMEOUT
        )
        if data_ok and controller_connected:
            self._transition(State.Standby)

    def _handle_standby(self, raw_axes, pm_state):
        raw_alt = self._mapper.get_raw_altitude_input(raw_axes)
        above = raw_alt > _ALTITUDE_AXIS_TAKEOFF_THRESHOLD
        if above:
            if pm_state is not None and pm_state != _PM_STATE_LOW_POWER:
                self._z_target = 0.0
                self._alt_above_threshold_prev = False
                self._transition(State.TakeOff)
            elif not self._alt_above_threshold_prev:
                # Rising edge — log blocking reason once
                if pm_state is None:
                    logger.warning("Takeoff blocked: no battery state reading")
                else:
                    logger.warning("Takeoff blocked: battery in low-power state (pm.state=%d)", pm_state)
        self._alt_above_threshold_prev = above

    def _handle_takeoff(self, data_ok, altitude, pm_state):
        if not data_ok:
            self._transition(State.CrazyflieError)
            return
        if pm_state is not None and pm_state == _PM_STATE_LOW_POWER:
            self._transition(State.Landing, reason="battery low-power state")
            return

        self._z_target = min(self._z_target + _TAKEOFF_RATE * _LOOP_DT, _TAKEOFF_TARGET_ALT)
        self._cf.send_hover_setpoint(0.0, 0.0, 0.0, self._z_target)

        if altitude is not None and altitude > _TAKEOFF_ALT_THRESHOLD:
            self._transition(State.Flying)

    def _handle_flying(self, raw_axes, last_event, data_ok, altitude, xy_speed, pm_state, now):
        # Check CF data outage
        if not data_ok:
            self._transition(State.CrazyflieError)
            return

        # Check controller outage → ControllerError
        if last_event is None or (now - last_event) > _CONTROLLER_OUTAGE_TIMEOUT:
            self._controller_error_start = now
            self._transition(State.ControllerError)
            return

        # Battery check
        if pm_state is not None and pm_state == _PM_STATE_LOW_POWER:
            self._transition(State.Landing, reason="battery low-power state")
            return

        # Altitude floor
        if altitude is not None and altitude < _LANDING_ALT_THRESHOLD:
            self._transition(State.Landing, reason=f"altitude {altitude:.2f} m below {_LANDING_ALT_THRESHOLD} m")
            return

        # Safety violation checks
        violation = False
        violation_reason = None
        if altitude is not None and altitude > _SAFETY_ALT_LIMIT:
            violation = True
            violation_reason = f"altitude {altitude:.2f} m exceeded safety limit {_SAFETY_ALT_LIMIT} m"
        if xy_speed is not None and xy_speed > _SAFETY_XY_SPEED_LIMIT:
            violation = True
            violation_reason = f"xy speed {xy_speed:.2f} m/s exceeded safety limit {_SAFETY_XY_SPEED_LIMIT} m/s"

        if violation:
            if self._safety_violation_start is None:
                self._safety_violation_start = now
            elif (now - self._safety_violation_start) > _SAFETY_VIOLATION_DURATION:
                self._safety_violation_start = None
                self._transition(State.Landing, reason=violation_reason)
                return
        else:
            self._safety_violation_start = None

        # Get flight commands
        cmds = self._mapper.map(raw_axes)

        # All-zero check
        all_zero = (cmds.altitude_rate == 0.0 and cmds.yaw_rate == 0.0 and
                    cmds.velocity_x == 0.0 and cmds.velocity_y == 0.0)
        if all_zero:
            if self._all_zero_start is None:
                self._all_zero_start = now
            elif (now - self._all_zero_start) > _ALL_ZERO_TIMEOUT:
                self._all_zero_start = None
                self._transition(State.Landing, reason="all-zero input for >10 s")
                return
        else:
            self._all_zero_start = None

        # Clamp altitude rate and update z_target
        alt_rate = max(-_MAX_ALTITUDE_RATE, min(_MAX_ALTITUDE_RATE, cmds.altitude_rate))
        self._z_target = max(_Z_TARGET_MIN, min(_Z_TARGET_MAX, self._z_target + alt_rate * _LOOP_DT))

        # Clamp xy speed
        vx = cmds.velocity_x
        vy = cmds.velocity_y
        speed = math.sqrt(vx ** 2 + vy ** 2)
        if speed > _MAX_XY_SPEED:
            scale = _MAX_XY_SPEED / speed
            vx *= scale
            vy *= scale

        self._cf.send_hover_setpoint(vx, vy, cmds.yaw_rate, self._z_target)

    def _handle_landing(self, data_ok):
        if not data_ok:
            self._transition(State.CrazyflieError)
            return

        self._z_target = max(0.0, self._z_target - _LANDING_RATE * _LOOP_DT)
        if self._z_target <= _LANDING_STOP_ALT:
            self._cf.send_stop()
            self._z_target = 0.0
            self._transition(State.Standby)
        else:
            self._cf.send_hover_setpoint(0.0, 0.0, 0.0, self._z_target)

    def _handle_cf_error(self, data_ok):
        # No commands sent
        if data_ok:
            self._transition(State.Standby)

    def _handle_controller_error(self, last_event, data_ok, now):
        if not data_ok:
            self._transition(State.CrazyflieError)
            return

        # Hold current z_target, zero velocity
        self._cf.send_hover_setpoint(0.0, 0.0, 0.0, self._z_target)

        # Controller reconnected?
        if last_event is not None and (now - last_event) <= _CONTROLLER_OUTAGE_TIMEOUT:
            self._transition(State.Flying)
            return

        # Auto-land after timeout
        if self._controller_error_start is not None:
            if (now - self._controller_error_start) > _CONTROLLER_ERROR_LAND_TIMEOUT:
                self._transition(State.Landing, reason="controller error timeout")
