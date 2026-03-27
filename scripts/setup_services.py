import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.sudo_helper import run_sudo

_SERVICE_NAME = "crazypilot"
_SERVICE_PATH = f"/etc/systemd/system/{_SERVICE_NAME}.service"
_CRAZYPILOT_BIN = "/usr/local/bin/crazypilot"


def _generate_service_unit(username: str) -> str:
    return f"""[Unit]
Description=Crazypilot drone controller
After=bluetooth.target

[Service]
ExecStart={_CRAZYPILOT_BIN}
Restart=always
User={username}

[Install]
WantedBy=multi-user.target
"""


def main():
    print("=== Setup Crazypilot systemd Service ===\n")

    username = os.getlogin()
    service_content = _generate_service_unit(username)

    print("Generated service unit:")
    print(service_content)

    # Write to a temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".service", delete=False) as tmp:
        tmp.write(service_content)
        tmp_path = tmp.name

    try:
        run_sudo(
            ["sudo", "cp", tmp_path, _SERVICE_PATH],
            f"Copy crazypilot.service to {_SERVICE_PATH}",
        )

        run_sudo(
            ["sudo", "systemctl", "daemon-reload"],
            "Reload systemd daemon to pick up the new service file",
        )

        run_sudo(
            ["sudo", "systemctl", "enable", _SERVICE_NAME],
            f"Enable {_SERVICE_NAME} service to start on boot",
        )
    finally:
        os.unlink(tmp_path)

    print(f"\nService '{_SERVICE_NAME}' is installed and enabled.")
    print("It will start automatically on the next boot.")
    print(f"To start it now: sudo systemctl start {_SERVICE_NAME}")


if __name__ == "__main__":
    main()
