import os
import time
import threading
import logging

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

logger = logging.getLogger("crazypilot")


class ControllerInput:
    def __init__(self, controller_name: str):
        self._controller_name = controller_name
        self._axes: dict[int, float] = {}
        self._lock = threading.Lock()
        self._last_event_time = None
        self._running = False
        self._thread = None
        self._joystick = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="controller-input")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def get_axes(self) -> dict:
        with self._lock:
            return dict(self._axes)

    def last_event_time(self):
        with self._lock:
            return self._last_event_time

    def _find_joystick(self):
        pygame.joystick.quit()
        pygame.joystick.init()
        count = pygame.joystick.get_count()
        for i in range(count):
            try:
                js = pygame.joystick.Joystick(i)
                js.init()
                if js.get_name() == self._controller_name:
                    logger.info("Controller connected: %s", self._controller_name)
                    return js
                js.quit()
            except Exception:
                pass
        return None

    def _run(self):
        pygame.init()
        pygame.joystick.init()
        pygame.event.set_allowed([pygame.JOYAXISMOTION, pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED])

        while self._running:
            if self._joystick is None:
                self._joystick = self._find_joystick()
                if self._joystick is None:
                    time.sleep(1.0)
                    continue

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.JOYAXISMOTION:
                    with self._lock:
                        self._axes[event.axis] = event.value
                        self._last_event_time = time.monotonic()
                elif event.type == pygame.JOYDEVICEREMOVED:
                    logger.warning("Controller disconnected: %s", self._controller_name)
                    # Do NOT clear axes — last values must persist (CP-026)
                    try:
                        self._joystick.quit()
                    except Exception:
                        pass
                    self._joystick = None
                elif event.type == pygame.JOYDEVICEADDED:
                    # Re-check for our controller
                    candidate = self._find_joystick()
                    if candidate is not None:
                        self._joystick = candidate

            time.sleep(0.005)
