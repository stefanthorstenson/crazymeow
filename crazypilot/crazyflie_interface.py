import time
import threading
import logging

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig

logger = logging.getLogger("crazypilot")

_DATA_STALE_TIMEOUT = 0.5  # seconds


class CrazyflieInterface:
    def __init__(self, uri: str):
        self._uri = uri
        self._lock = threading.Lock()
        self._z = None
        self._vx = None
        self._vy = None
        self._vbat = None
        self._last_data_time = None
        self._connected = False
        self._running = False
        self._thread = None
        self._cf = None
        self._log_config = None

    def start(self):
        cflib.crtp.init_drivers(enable_debug_driver=False)
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="cf-interface")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)

    def is_connected(self) -> bool:
        with self._lock:
            return self._connected

    def is_data_ok(self) -> bool:
        with self._lock:
            if self._last_data_time is None:
                return False
            return (time.monotonic() - self._last_data_time) <= _DATA_STALE_TIMEOUT

    def get_altitude(self):
        with self._lock:
            return self._z

    def get_xy_speed(self):
        with self._lock:
            if self._vx is None or self._vy is None:
                return None
            return (self._vx ** 2 + self._vy ** 2) ** 0.5

    def get_battery_voltage(self):
        with self._lock:
            return self._vbat

    def send_hover_setpoint(self, vx: float, vy: float, yaw_rate: float, z_target: float):
        cf = self._cf
        if cf is not None:
            try:
                cf.commander.send_hover_setpoint(vx, vy, yaw_rate, z_target)
            except Exception as e:
                logger.warning("send_hover_setpoint failed: %s", e)

    def send_stop(self):
        cf = self._cf
        if cf is not None:
            try:
                cf.commander.send_stop_setpoint()
            except Exception as e:
                logger.warning("send_stop failed: %s", e)

    def _run(self):
        while self._running:
            logger.info("Connecting to Crazyflie at %s", self._uri)
            cf = Crazyflie(rw_cache="./cache")
            self._cf = cf
            cf.connected.add_callback(self._on_connected)
            cf.disconnected.add_callback(self._on_disconnected)
            cf.connection_failed.add_callback(self._on_connection_failed)

            cf.open_link(self._uri)

            # Wait until disconnected or stopped
            while self._running and self._cf is cf:
                time.sleep(0.1)

            time.sleep(2.0)

    def _on_connected(self, uri: str):
        logger.info("Crazyflie connected: %s", uri)
        with self._lock:
            self._connected = True

        log_config = LogConfig("StateEstimate", period_in_ms=20)
        log_config.add_variable("stateEstimate.z", "float")
        log_config.add_variable("stateEstimate.vx", "float")
        log_config.add_variable("stateEstimate.vy", "float")
        log_config.add_variable("pm.vbat", "float")

        self._log_config = log_config
        try:
            self._cf.log.add_config(log_config)
            log_config.data_received_cb.add_callback(self._on_log_data)
            log_config.start()
            logger.info("Log config started")
        except Exception as e:
            logger.error("Failed to start log config: %s", e)

    def _on_disconnected(self, uri: str):
        logger.warning("Crazyflie disconnected: %s", uri)
        with self._lock:
            self._connected = False
            self._last_data_time = None

        if self._log_config is not None:
            try:
                self._log_config.stop()
                self._log_config.delete()
            except Exception:
                pass
            self._log_config = None

        self._cf = None

    def _on_connection_failed(self, uri: str, msg: str):
        logger.warning("Crazyflie connection failed: %s — %s", uri, msg)
        with self._lock:
            self._connected = False
        self._cf = None

    def _on_log_data(self, timestamp, data, log_config):
        with self._lock:
            self._z = data.get("stateEstimate.z")
            self._vx = data.get("stateEstimate.vx")
            self._vy = data.get("stateEstimate.vy")
            self._vbat = data.get("pm.vbat")
            self._last_data_time = time.monotonic()
