import sys
import subprocess


def run_sudo(cmd: list, description: str):
    print(f"\n[sudo] {description}")
    print(f"  Command: {' '.join(cmd)}")

    try:
        confirm = input("Proceed? [y/N]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        sys.exit(0)

    if confirm != "y":
        print("Skipped.")
        return

    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: {' '.join(cmd)}"
        )
