"""
RankedDST/tools/logger.py

This module contains the global logger object to be imported by the rest of the program
"""

# RankedDST/tools/logger.py
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

LOG_DIR = Path.home() / "ranked_dst" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def initialize_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    log_file = LOG_DIR / f"{datetime.now().date()}-{name}.log"

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        fh = logging.FileHandler(log_file, encoding="utf-8")

        fmt = logging.Formatter(
            "[%(asctime)s] [%(levelname)s]: %(message)s"
        )
        fh.setFormatter(fmt)

        logger.addHandler(fh)

        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    return logger

logger = initialize_logger("app")
server_logger = initialize_logger("dedi-server")
