"""
RankedDST/dedicated_server/world_cleanup.py

This module is tasked with zipping up old ranked DST worlds and moving them to a
new location. Up to 5 will be kept. The rest are deleted.
"""
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import zipfile
import re

import RankedDST.tools.state as state
from RankedDST.tools.logger import logger, LOG_DIR

NUM_SAVES = 5

MATCH_RE = re.compile(r"^Ranked DST Match (\d+)$")

def _extract_match_number(path: Path) -> int | None:
    """
    Extracts match number from 'Ranked DST Match <int>' folders.
    Returns None if not a valid match folder.
    """
    name = path.stem if path.suffix == ".zip" else path.name
    m = MATCH_RE.match(name)
    if not m:
        return None
    return int(m.group(1))


def _zip_directory(src: Path, dst_zip: Path) -> None:
    with zipfile.ZipFile(dst_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in src.rglob("*"):
            zf.write(p, p.relative_to(src))


def clean_old_files() -> None:
    """
    1. Move ALL 'Ranked DST Match *' folders into 'Past Ranked Matches' as ZIPs
    2. In 'Past Ranked Matches', keep only the 5 most recent ZIPs
       (by match number), delete the rest
    3. Delete 1 week old logs
    """
    
    
    log_path = Path(LOG_DIR)
    if log_path.exists():
        logger.info("Cleaning 1 week old logs")
        cutoff_date = datetime.now().date() - timedelta(days=7)

        for log_file in log_path.glob("*.log"):
            try:
                date_str = log_file.name.split("-")[0:3]
                date_str = "-".join(date_str)  # YYYY-MM-DD
                log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception:
                logger.warning(f"Skipping unexpected log format: {log_file.name}")
                continue

            if log_date < cutoff_date:
                try:
                    logger.info(f"Deleting old log: {log_file.name}")
                    log_file.unlink()
                except Exception as e:
                    logger.error(f"Failed to delete {log_file.name}: {e}")

    logger.info("Cleaning old Ranked DST matches (simple mode)...")

    base_dir = state.get_user_data(get_key="cluster_path")
    if not isinstance(base_dir, str) or not base_dir:
        logger.debug("Cannot cleanup without a cluster path")
        return
    
    base_dir = Path(base_dir)

    # base_dir = Path.home() / "Documents" / "Klei" / "DoNotStarveTogether"
    past_dir = base_dir / "Past Ranked Matches"
    past_dir.mkdir(exist_ok=True)

    for p in base_dir.iterdir():
        if not p.is_dir():
            continue

        match_num = _extract_match_number(p)
        if match_num is None:
            continue

        zip_path = past_dir / f"{p.name}.zip"

        logger.info(f"Archiving {p.name} -> {zip_path.name}")

        if not zip_path.exists():
            _zip_directory(p, zip_path)

        shutil.rmtree(p, ignore_errors=True)

    zips: list[Path] = []

    for p in past_dir.iterdir():
        if not p.is_file():
            continue

        match_num = _extract_match_number(p)
        if match_num is not None:
            zips.append(p)

    # Sort newest to oldest
    zips.sort(
        key=lambda p: _extract_match_number(p),
        reverse=True,
    )

    logger.info(f"Found {len(zips)} archived matches")

    # Delete everything beyond the newest NUM_SAVES
    for old_zip in zips[NUM_SAVES:]:
        logger.info(f"Deleting old archive {old_zip.name}")
        old_zip.unlink(missing_ok=True)
