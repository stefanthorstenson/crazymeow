import sys
import subprocess


def clone(url: str, target: str, description: str = ""):
    print(f"\n[git clone] {description}" if description else "\n[git clone]")
    print(f"  Repository: {url}")
    print(f"  Target:     {target}")

    try:
        confirm = input("Proceed? [y/N]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        sys.exit(0)

    if confirm != "y":
        print("Skipped.")
        return

    result = subprocess.run(["git", "clone", url, target])
    if result.returncode != 0:
        raise RuntimeError(
            f"git clone failed with exit code {result.returncode}: {url} → {target}"
        )
