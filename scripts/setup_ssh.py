import sys
import os
import socket

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.sudo_helper import run_sudo


def _get_ip_addresses() -> list:
    addrs = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            addr = info[4][0]
            if addr not in addrs and not addr.startswith("127.") and ":" not in addr:
                addrs.append(addr)
    except Exception:
        pass
    return addrs


def main():
    print("=== Enable SSH on Raspberry Pi ===\n")

    run_sudo(
        ["sudo", "systemctl", "enable", "ssh"],
        "Enable SSH service to start automatically on boot",
    )

    run_sudo(
        ["sudo", "systemctl", "start", "ssh"],
        "Start the SSH service now",
    )

    print("\nSSH is enabled and running.")

    ips = _get_ip_addresses()
    if ips:
        print("You can connect via:")
        for ip in ips:
            print(f"  ssh {os.getenv('USER', 'pi')}@{ip}")
    else:
        print("Could not determine IP address. Check with: hostname -I")


if __name__ == "__main__":
    main()
