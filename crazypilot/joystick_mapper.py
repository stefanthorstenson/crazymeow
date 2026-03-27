from collections import namedtuple

FlightCommands = namedtuple("FlightCommands", ["altitude_rate", "yaw_rate", "velocity_x", "velocity_y"])

_DEADZONE = 0.05
_MAX_ALTITUDE_RATE = 0.3   # m/s
_MAX_YAW_RATE = 45.0       # deg/s
_MAX_VELOCITY_XY = 1.0     # m/s


def _apply_deadzone(value: float) -> float:
    if abs(value) < _DEADZONE:
        return 0.0
    # Scale so output reaches 1.0 at full deflection
    sign = 1.0 if value > 0 else -1.0
    return sign * (abs(value) - _DEADZONE) / (1.0 - _DEADZONE)


class JoystickMapper:
    def __init__(self, mapping: dict):
        self._axes = mapping["axes"]

    def _get_raw_value(self, role: str, raw_axes: dict) -> float:
        cfg = self._axes[role]
        idx = cfg["index"]
        value = raw_axes.get(idx, 0.0)
        if cfg["inverted"]:
            value = -value
        return value

    def get_raw_altitude_input(self, raw_axes: dict) -> float:
        return self._get_raw_value("altitude_rate", raw_axes)

    def map(self, raw_axes: dict) -> FlightCommands:
        altitude_raw = _apply_deadzone(self._get_raw_value("altitude_rate", raw_axes))
        yaw_raw = _apply_deadzone(self._get_raw_value("yaw_rate", raw_axes))
        vx_raw = _apply_deadzone(self._get_raw_value("velocity_x", raw_axes))
        vy_raw = _apply_deadzone(self._get_raw_value("velocity_y", raw_axes))

        altitude_rate = altitude_raw * _MAX_ALTITUDE_RATE
        yaw_rate = yaw_raw * _MAX_YAW_RATE
        velocity_x = vx_raw * _MAX_VELOCITY_XY
        velocity_y = vy_raw * _MAX_VELOCITY_XY

        return FlightCommands(
            altitude_rate=altitude_rate,
            yaw_rate=yaw_rate,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
        )
