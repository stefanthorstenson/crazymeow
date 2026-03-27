import sys
import os
import subprocess
import venv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.sudo_helper import run_sudo
from utils.git_helper import clone

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REQUIREMENTS_TXT = os.path.join(_REPO_ROOT, "requirements.txt")
_VENV_DIR = os.path.join(_REPO_ROOT, ".venv")
_VENV_PYTHON = os.path.join(_VENV_DIR, "bin", "python")
_UDEV_RULES_SRC = os.path.join(_REPO_ROOT, "scripts", "99-bitcraze.rules")
_UDEV_RULES_DST = "/etc/udev/rules.d/99-bitcraze.rules"

_SYSTEM_PACKAGES = [
    "python3-venv",
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

    # Install udev rules for Bitcraze USB devices
    print("\nInstalling udev rules for Bitcraze USB devices...")
    run_sudo(
        ["sudo", "cp", _UDEV_RULES_SRC, _UDEV_RULES_DST],
        f"Copy udev rules to {_UDEV_RULES_DST} (allows non-root USB access to Crazyflie and Crazyradio)",
    )
    run_sudo(
        ["sudo", "udevadm", "control", "--reload-rules"],
        "Reload udev rules",
    )
    run_sudo(
        ["sudo", "udevadm", "trigger"],
        "Apply udev rules to currently connected devices",
    )
    run_sudo(
        ["sudo", "usermod", "-aG", "plugdev", os.environ.get("SUDO_USER", os.environ["USER"])],
        "Add current user to plugdev group (required for USB access without sudo)",
    )

    # Create virtual environment
    if not os.path.isdir(_VENV_DIR):
        print(f"\nCreating virtual environment at {_VENV_DIR}...")
        venv.create(_VENV_DIR, with_pip=True)
    else:
        print(f"\nVirtual environment already exists at {_VENV_DIR}")

    # Install Python packages into venv
    print("\nInstalling Python packages into virtual environment...")
    result = subprocess.run(
        [_VENV_PYTHON, "-m", "pip", "install", "-r", _REQUIREMENTS_TXT]
    )
    if result.returncode != 0:
        print("pip install failed.")
        sys.exit(1)

    # Install the crazymeow package itself into venv
    print("\nInstalling crazymeow package into virtual environment...")
    result = subprocess.run(
        [_VENV_PYTHON, "-m", "pip", "install", "-e", _REPO_ROOT]
    )
    if result.returncode != 0:
        print("Package install failed.")
        sys.exit(1)

    print("\nAll dependencies installed.")
    print(f"Virtual environment: {_VENV_DIR}")
    print(f"Activate with: source {_VENV_DIR}/bin/activate")


if __name__ == "__main__":
    main()
