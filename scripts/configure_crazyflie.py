import sys
import os
import json
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.mem import MemoryElement

_CONFIG_DIR = Path.home() / ".config" / "crazypilot"
_CONFIG_FILE = _CONFIG_DIR / "crazypilot_config.json"
_USB_URI = "usb://0"

_SPEED_STRINGS = {0: "250K", 1: "1M", 2: "2M"}


def _prompt_int(prompt: str, default: int) -> int:
    raw = input(f"{prompt} [{default}]: ").strip()
    if raw == "":
        return default
    return int(raw)


def _prompt_hex(prompt: str, default: int) -> int:
    raw = input(f"{prompt} [{hex(default)}]: ").strip()
    if raw == "":
        return default
    return int(raw, 16)


def main():
    print("=== Configure Crazyflie Radio ===")
    print("Connect the Crazyflie via USB and ensure it is running normal firmware.\n")

    channel = _prompt_int("Radio channel (0-125)", 80)
    speed_raw = _prompt_int("Radio speed (0=250K, 1=1M, 2=2M)", 2)
    if speed_raw not in (0, 1, 2):
        print("Invalid speed. Must be 0, 1, or 2.")
        sys.exit(1)
    address = _prompt_hex("Radio address (hex, e.g. 0xE7E7E7E7E7)", 0xE7E7E7E7E7)

    cflib.crtp.init_drivers(enable_debug_driver=False)

    read_done = threading.Event()
    write_done = threading.Event()
    cf_instance = {"cf": None, "mem": None}

    def connected_cb(uri):
        print(f"Connected to {uri}")
        mems = cf_instance["cf"].mem.get_mems(MemoryElement.TYPE_I2C)
        if not mems:
            print("No I2C memory found.")
            read_done.set()
            return
        mem = mems[0]
        cf_instance["mem"] = mem

        def read_cb(mem_obj):
            print(f"Current EEPROM: channel={mem_obj.elements.get('radio_channel')}, "
                  f"speed={mem_obj.elements.get('radio_speed')}, "
                  f"address={hex(mem_obj.elements.get('radio_address', 0))}")
            read_done.set()

        mem.update(read_cb)

    def disconnected_cb(uri):
        print(f"Disconnected from {uri}")
        read_done.set()
        write_done.set()

    def connection_failed_cb(uri, msg):
        print(f"Connection failed: {uri} — {msg}")
        read_done.set()
        write_done.set()

    cf = Crazyflie(rw_cache="./cache")
    cf_instance["cf"] = cf
    cf.connected.add_callback(connected_cb)
    cf.disconnected.add_callback(disconnected_cb)
    cf.connection_failed.add_callback(connection_failed_cb)

    print(f"Connecting to {_USB_URI}...")
    cf.open_link(_USB_URI)
    read_done.wait(timeout=10.0)

    mem = cf_instance["mem"]
    if mem is None:
        print("Failed to read EEPROM.")
        cf.close_link()
        sys.exit(1)

    print(f"\nWriting: channel={channel}, speed={speed_raw} ({_SPEED_STRINGS[speed_raw]}), "
          f"address={hex(address)}")

    mem.elements["radio_channel"] = channel
    mem.elements["radio_speed"] = speed_raw
    mem.elements["radio_address"] = address
    mem.elements["version"] = 1

    def write_cb(mem_obj):
        print("EEPROM write successful.")
        write_done.set()

    mem.write_data(write_cb)
    write_done.wait(timeout=10.0)

    cf.close_link()

    # Build URI
    speed_str = _SPEED_STRINGS[speed_raw]
    address_hex = format(address, "X").upper()
    uri = f"radio://0/{channel}/{speed_str}/{address_hex}"
    print(f"\nResulting URI: {uri}")

    # Save to config
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_FILE, "w") as f:
        json.dump({"crazyflie_uri": uri}, f, indent=2)
        f.write("\n")
    print(f"URI saved to {_CONFIG_FILE}")
    print("\nIMPORTANT: Power-cycle the Crazyflie for the new radio settings to take effect.")


if __name__ == "__main__":
    main()
