"""
RankedDST/tools/logger.py

This module contains the global logger object to be imported by the rest of the program
"""

# RankedDST/tools/logger.py
import logging
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / f"{datetime.now().date()}.log"

logger = logging.getLogger("app")

if not logger.handlers:
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(log_file, encoding="utf-8")

    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
    )
    fh.setFormatter(fmt)

    logger.addHandler(fh)
