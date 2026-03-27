import sys
import os
import json
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path

import cflib.crtp
from cflib.crazyflie import Crazyflie

_CONFIG_FILE = Path.home() / ".config" / "crazypilot" / "crazypilot_config.json"
_CONNECT_TIMEOUT = 10.0


def main():
    print("=== Test Crazyflie Connection ===\n")

    if not _CONFIG_FILE.exists():
        print(f"Config file not found: {_CONFIG_FILE}")
        print("Run configure_crazyflie.py first.")
        sys.exit(1)

    with open(_CONFIG_FILE) as f:
        cfg = json.load(f)

    uri = cfg.get("crazyflie_uri")
    if not uri:
        print(f"'crazyflie_uri' not found in {_CONFIG_FILE}")
        sys.exit(1)

    print(f"Testing connection to: {uri}")

    cflib.crtp.init_drivers(enable_debug_driver=False)

    connected_event = threading.Event()
    failed_event = threading.Event()
    result = {"success": False}

    def connected_cb(link_uri):
        result["success"] = True
        connected_event.set()

    def connection_failed_cb(link_uri, msg):
        result["msg"] = msg
        failed_event.set()

    def disconnected_cb(link_uri):
        pass

    cf = Crazyflie()
    cf.connected.add_callback(connected_cb)
    cf.connection_failed.add_callback(connection_failed_cb)
    cf.disconnected.add_callback(disconnected_cb)

    cf.open_link(uri)

    done = threading.Event()

    def wait():
        idx = [connected_event, failed_event]
        for ev in idx:
            ev.wait(timeout=_CONNECT_TIMEOUT)
            if ev.is_set():
                break
        done.set()

    import threading as _threading
    t = _threading.Thread(target=wait, daemon=True)
    t.start()

    connected_event.wait(timeout=_CONNECT_TIMEOUT) or failed_event.wait(timeout=0.1)

    if result.get("success"):
        print(f"PASS: Successfully connected to {uri}")
        cf.close_link()
        sys.exit(0)
    else:
        msg = result.get("msg", "timeout")
        print(f"FAIL: Could not connect to {uri} — {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
