import sys
import time
import pygame

_DEADZONE = 0.05
_MAX_ALTITUDE_RATE = 0.3
_MAX_YAW_RATE = 45.0
_MAX_VELOCITY_XY = 1.0


def _apply_deadzone(value: float) -> float:
    if abs(value) < _DEADZONE:
        return 0.0
    sign = 1.0 if value > 0 else -1.0
    return sign * (abs(value) - _DEADZONE) / (1.0 - _DEADZONE)


def run_live_test(joystick, mapping: dict):
    axes_cfg = mapping["axes"]
    print("\nLive test mode. Move the sticks to verify the mapping.")
    print("Press Ctrl+C or 'q' + Enter to exit.\n")

    try:
        while True:
            pygame.event.pump()

            raw = {}
            for i in range(joystick.get_numaxes()):
                raw[i] = joystick.get_axis(i)

            def get_mapped(role):
                cfg = axes_cfg[role]
                v = raw.get(cfg["index"], 0.0)
                if cfg["inverted"]:
                    v = -v
                return _apply_deadzone(v)

            altitude_rate = get_mapped("altitude_rate") * _MAX_ALTITUDE_RATE
            yaw_rate = get_mapped("yaw_rate") * _MAX_YAW_RATE
            velocity_x = get_mapped("velocity_x") * _MAX_VELOCITY_XY
            velocity_y = get_mapped("velocity_y") * _MAX_VELOCITY_XY

            raw_str = "  ".join(f"ax{i}:{v:+.2f}" for i, v in sorted(raw.items()))
            cmd_str = (
                f"alt_rate:{altitude_rate:+.3f}m/s  "
                f"yaw:{yaw_rate:+.1f}deg/s  "
                f"vx:{velocity_x:+.3f}m/s  "
                f"vy:{velocity_y:+.3f}m/s"
            )
            print(f"\r  Raw: [{raw_str}]  Cmds: [{cmd_str}]    ", end="", flush=True)

            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nLive test ended.")
