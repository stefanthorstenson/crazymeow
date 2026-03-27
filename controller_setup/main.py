import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from controller_setup.controller_detector import detect_and_select
from controller_setup.axis_mapper import map_axes
from controller_setup.config_writer import save
from controller_setup.live_tester import run_live_test


def main():
    print("=== Controller Mapping Setup ===\n")

    pygame.init()
    pygame.joystick.init()

    # Step 1: Detect and select controller
    try:
        joystick, controller_name = detect_and_select()
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error detecting controllers: {e}")
        sys.exit(1)

    # Step 2: Map axes
    try:
        axes = map_axes(joystick)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error during axis mapping: {e}")
        sys.exit(1)

    mapping = {
        "controller_name": controller_name,
        "axes": axes,
    }

    # Step 3: Show summary and ask for confirmation
    print("\n=== Mapping Summary ===")
    print(f"Controller: {controller_name}")
    for role, cfg in axes.items():
        inv = "inverted" if cfg["inverted"] else "normal"
        print(f"  {role}: axis {cfg['index']} ({inv})")

    try:
        confirm = input("\nSave this mapping? [y/N]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        sys.exit(0)

    if confirm != "y":
        print("Mapping not saved.")
        sys.exit(0)

    # Step 4: Save
    try:
        save(mapping)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error saving mapping: {e}")
        sys.exit(1)

    # Step 5: Offer live test
    try:
        run_test = input("Run live test to verify mapping? [y/N]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nDone.")
        sys.exit(0)

    if run_test == "y":
        try:
            run_live_test(joystick, mapping)
        except SystemExit:
            raise
        except Exception as e:
            print(f"Error during live test: {e}")
            sys.exit(1)

    print("Done.")
    pygame.quit()
