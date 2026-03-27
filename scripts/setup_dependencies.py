import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.sudo_helper import run_sudo
from utils.git_helper import clone

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REQUIREMENTS_TXT = os.path.join(_REPO_ROOT, "requirements.txt")

_SYSTEM_PACKAGES = [
    "python3-pygame",
    "python3-pip",
    "libusb-1.0-0",
]


def main():
    print("=== Setup Dependencies ===\n")

    # Install system packages
    print("Installing system packages...")
    run_sudo(
        ["sudo", "apt-get", "install", "-y"] + _SYSTEM_PACKAGES,
        f"Install system packages: {', '.join(_SYSTEM_PACKAGES)}",
    )

    # Install Python packages from requirements.txt
    print("\nInstalling Python packages from requirements.txt...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", _REQUIREMENTS_TXT]
    )
    if result.returncode != 0:
        print("pip install failed.")
        sys.exit(1)

    print("\nAll dependencies installed.")


if __name__ == "__main__":
    main()
