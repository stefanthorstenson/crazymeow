import logging
import os
import sys
import time
import threading
from datetime import datetime, timezone
from pathlib import Path


def setup_logging(debug: bool = False) -> logging.Logger:
    log_dir = Path.home() / ".local" / "share" / "crazypilot" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"crazypilot_{timestamp}.log"

    logger = logging.getLogger("crazypilot")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(module)s %(message)s")
    fmt.converter = time.gmtime

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    if debug:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(fmt)
        logger.addHandler(stdout_handler)
    else:
        stderr_handler = logging.StreamHandler()
        stderr_handler.setLevel(logging.WARNING)
        stderr_handler.setFormatter(fmt)
        logger.addHandler(stderr_handler)

    start_log_rotation(str(log_dir))

    return logger


def start_log_rotation(log_dir: str):
    def _rotate():
        while True:
            time.sleep(300)
            cutoff = time.time() - 86400
            try:
                for entry in os.scandir(log_dir):
                    if entry.is_file() and entry.stat().st_mtime < cutoff:
                        os.remove(entry.path)
            except Exception:
                pass

    t = threading.Thread(target=_rotate, daemon=True, name="log-rotation")
    t.start()
