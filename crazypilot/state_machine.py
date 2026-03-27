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

_BATTERY_TAKEOFF_MIN = 3.5     # V
_BATTERY_LANDING_THRESHOLD = 3.35  # V

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
        now = time.monotonic()

        if state == State.Initializing:
            self._handle_initializing(data_ok, last_event, now)

        elif state == State.Standby:
            self._handle_standby(raw_axes, battery)

        elif state == State.TakeOff:
            self._handle_takeoff(data_ok, altitude, battery)

        elif state == State.Flying:
            self._handle_flying(raw_axes, last_event, data_ok, altitude, xy_speed, battery, now)

        elif state == State.Landing:
            self._handle_landing(data_ok)

        elif state == State.CrazyflieError:
            self._handle_cf_error(data_ok)

        elif state == State.ControllerError:
            self._handle_controller_error(last_event, data_ok, now)

    def _transition(self, new_state: State):
        logger.info("State: %s → %s", self._state.name, new_state.name)
        self._state = new_state

    # -------------------------------------------------------------------------
    # State handlers
    # -------------------------------------------------------------------------

    def _handle_initializing(self, data_ok, last_event, now):
        controller_connected = (
            last_event is not None and (now - last_event) <= _CONTROLLER_OUTAGE_TIMEOUT
        )
        if data_ok and controller_connected:
            self._transition(State.Standby)

    def _handle_standby(self, raw_axes, battery):
        raw_alt = self._mapper.get_raw_altitude_input(raw_axes)
        if raw_alt > _ALTITUDE_AXIS_TAKEOFF_THRESHOLD:
            if battery is not None and battery > _BATTERY_TAKEOFF_MIN:
                self._z_target = 0.0
                self._transition(State.TakeOff)

    def _handle_takeoff(self, data_ok, altitude, battery):
        if not data_ok:
            self._transition(State.CrazyflieError)
            return
        if battery is not None and battery < _BATTERY_LANDING_THRESHOLD:
            self._transition(State.Landing)
            return

        self._z_target = min(self._z_target + _TAKEOFF_RATE * _LOOP_DT, _TAKEOFF_TARGET_ALT)
        self._cf.send_hover_setpoint(0.0, 0.0, 0.0, self._z_target)

        if altitude is not None and altitude > _TAKEOFF_ALT_THRESHOLD:
            self._transition(State.Flying)

    def _handle_flying(self, raw_axes, last_event, data_ok, altitude, xy_speed, battery, now):
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
        if battery is not None and battery < _BATTERY_LANDING_THRESHOLD:
            self._transition(State.Landing)
            return

        # Altitude floor
        if altitude is not None and altitude < _LANDING_ALT_THRESHOLD:
            self._transition(State.Landing)
            return

        # Safety violation checks
        violation = False
        if altitude is not None and altitude > _SAFETY_ALT_LIMIT:
            violation = True
        if xy_speed is not None and xy_speed > _SAFETY_XY_SPEED_LIMIT:
            violation = True

        if violation:
            if self._safety_violation_start is None:
                self._safety_violation_start = now
            elif (now - self._safety_violation_start) > _SAFETY_VIOLATION_DURATION:
                logger.warning("Safety violation exceeded 1s — transitioning to Landing")
                self._safety_violation_start = None
                self._transition(State.Landing)
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
                logger.info("All-zero input for >10s — transitioning to Landing")
                self._all_zero_start = None
                self._transition(State.Landing)
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
                self._transition(State.Landing)
