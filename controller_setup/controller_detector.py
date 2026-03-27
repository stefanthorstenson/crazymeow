import sys
import pygame


def detect_and_select() -> tuple:
    pygame.joystick.init()
    count = pygame.joystick.get_count()

    if count == 0:
        print("No controllers detected. Connect a Bluetooth controller and try again.")
        sys.exit(1)

    joysticks = []
    for i in range(count):
        js = pygame.joystick.Joystick(i)
        js.init()
        joysticks.append(js)

    print("Detected controllers:")
    for i, js in enumerate(joysticks):
        print(f"  {i + 1}. {js.get_name()}")

    while True:
        try:
            choice = input(f"Select controller [1-{count}]: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < count:
                selected = joysticks[idx]
                name = selected.get_name()
                print(f"Selected: {name}")
                return selected, name
            else:
                print(f"Please enter a number between 1 and {count}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)
