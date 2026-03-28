import sys
import time
import pygame

_AXIS_ROLES = [
    ("altitude_rate", "Push the LEFT stick UP for altitude rate, then release."),
    ("yaw_rate", "Push the LEFT stick LEFT for yaw rate (positive direction), then release."),
    ("velocity_x", "Push the RIGHT stick UP for forward velocity, then release."),
    ("velocity_y", "Push the RIGHT stick LEFT for positive y velocity (left), then release."),
]

_DETECTION_THRESHOLD = 0.3
_ZERO_THRESHOLD = 0.1


def _get_all_axes(joystick) -> dict:
    pygame.event.pump()
    axes = {}
    for i in range(joystick.get_numaxes()):
        axes[i] = joystick.get_axis(i)
    return axes


def map_axes(joystick) -> dict:
    result = {}

    for role, instruction in _AXIS_ROLES:
        print(f"\n--- Mapping: {role} ---")
        print(instruction)
        print("(Press Ctrl+C to abort)")

        detected_index = None
        detected_inverted = None

        baseline = _get_all_axes(joystick)

        # Wait for a significant axis movement
        while detected_index is None:
            try:
                axes = _get_all_axes(joystick)
                # Show live values
                values_str = "  ".join(f"ax{i}:{v:+.2f}" for i, v in sorted(axes.items()))
                print(f"\r  Live: {values_str}    ", end="", flush=True)

                for idx, value in axes.items():
                    delta = value - baseline.get(idx, 0.0)
                    if abs(delta) > _DETECTION_THRESHOLD:
                        detected_index = idx
                        # Positive delta = not inverted (expected positive direction)
                        detected_inverted = delta < 0
                        break

                time.sleep(0.02)
            except KeyboardInterrupt:
                print("\nAborted.")
                sys.exit(0)

        print(f"\n  Detected axis {detected_index} (inverted={detected_inverted})")

        result[role] = {
            "index": detected_index,
            "inverted": detected_inverted,
        }

        # Wait for axis to return near zero before proceeding
        print("  Release the stick...")
        while True:
            try:
                axes = _get_all_axes(joystick)
                if abs(axes.get(detected_index, 0.0)) < _ZERO_THRESHOLD:
                    break
                time.sleep(0.05)
            except KeyboardInterrupt:
                print("\nAborted.")
                sys.exit(0)

    return result
