import argparse
import os
import threading
from pathlib import Path

from crazypilot.logger import setup_logging
from crazypilot.config_loader import load_controller_mapping, load_crazyflie_uri
from crazypilot.controller_input import ControllerInput
from crazypilot.crazyflie_interface import CrazyflieInterface
from crazypilot.joystick_mapper import JoystickMapper
from crazypilot.state_machine import StateMachine

_DEFAULT_MAPPING = str(Path.home() / ".config" / "crazypilot" / "controller_mapping.json")


def main():
    parser = argparse.ArgumentParser(description="Crazypilot drone controller")
    parser.add_argument(
        "--controller-mapping",
        default=_DEFAULT_MAPPING,
        metavar="PATH",
        help="Path to controller_mapping.json (default: %(default)s)",
    )
    args = parser.parse_args()

    logger = setup_logging()
    logger.info("Crazypilot starting up")

    try:
        mapping = load_controller_mapping(args.controller_mapping)
    except Exception as e:
        logger.error("Failed to load controller mapping: %s", e)
        raise SystemExit(1)

    try:
        uri = load_crazyflie_uri()
    except Exception as e:
        logger.error("Failed to load Crazyflie URI: %s", e)
        raise SystemExit(1)

    logger.info("Controller: %s", mapping["controller_name"])
    logger.info("Crazyflie URI: %s", uri)

    controller = ControllerInput(mapping["controller_name"])
    cf_interface = CrazyflieInterface(uri)
    mapper = JoystickMapper(mapping)
    state_machine = StateMachine(cf_interface, controller, mapper, config={})

    controller.start()
    cf_interface.start()

    sm_thread = threading.Thread(target=state_machine.run, daemon=True, name="state-machine")
    sm_thread.start()

    try:
        sm_thread.join()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt — shutting down")
    finally:
        state_machine.stop()
        controller.stop()
        cf_interface.stop()
        logger.info("Crazypilot stopped")
