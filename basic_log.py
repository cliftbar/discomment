import logging
from datetime import datetime

from config import env_vals

log_level: int = logging.getLevelName(str(env_vals.get("log_level", "INFO")).upper())


def log(msg: str, level: int = logging.INFO, source: str = None):
    if log_level <= level:
        before: str = f"{datetime.utcnow().isoformat()} {logging.getLevelName(level)}"
        if source is not None:
            before = f"{before} {source}"
        print(f"{before}: {msg}")
