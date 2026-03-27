import json
import os
from pathlib import Path

_REQUIRED_AXES = {"altitude_rate", "yaw_rate", "velocity_x", "velocity_y"}
_CONFIG_DIR = Path.home() / ".config" / "crazypilot"
_CF_CONFIG = _CONFIG_DIR / "crazypilot_config.json"


def load_controller_mapping(path: str) -> dict:
    with open(path, "r") as f:
        mapping = json.load(f)

    if "controller_name" not in mapping:
        raise ValueError(f"controller_mapping missing 'controller_name' in {path}")
    if "axes" not in mapping:
        raise ValueError(f"controller_mapping missing 'axes' in {path}")

    axes = mapping["axes"]
    missing = _REQUIRED_AXES - set(axes.keys())
    if missing:
        raise ValueError(f"controller_mapping missing axis entries: {missing} in {path}")

    for role, entry in axes.items():
        if "index" not in entry:
            raise ValueError(f"axis '{role}' missing 'index' in {path}")
        if "inverted" not in entry:
            raise ValueError(f"axis '{role}' missing 'inverted' in {path}")

    return mapping


def load_crazyflie_uri() -> str:
    if not _CF_CONFIG.exists():
        raise FileNotFoundError(
            f"Crazyflie config not found at {_CF_CONFIG}. "
            "Run configure_crazyflie script first."
        )
    with open(_CF_CONFIG, "r") as f:
        cfg = json.load(f)
    if "crazyflie_uri" not in cfg:
        raise ValueError(f"'crazyflie_uri' key missing in {_CF_CONFIG}")
    return cfg["crazyflie_uri"]
