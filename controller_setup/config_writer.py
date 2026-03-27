import json
import os
import sys
from pathlib import Path

_DEFAULT_PATH = str(Path.home() / ".config" / "crazypilot" / "controller_mapping.json")


def save(mapping: dict, path: str = None):
    if path is None:
        path = _DEFAULT_PATH

    config_dir = os.path.dirname(path)
    os.makedirs(config_dir, exist_ok=True)

    if os.path.exists(path):
        print(f"Warning: {path} already exists.")
        try:
            confirm = input("Overwrite? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)
        if confirm != "y":
            print("Not overwriting. Exiting.")
            sys.exit(0)

    with open(path, "w") as f:
        json.dump(mapping, f, indent=2)
        f.write("\n")

    print(f"Mapping saved to {path}")
