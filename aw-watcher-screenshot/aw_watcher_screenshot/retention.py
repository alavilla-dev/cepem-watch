"""Delete stored screenshots older than the configured retention period."""
import logging
import os
import shutil
from datetime import datetime, timedelta

from .capture import images_root

logger = logging.getLogger(__name__)


def purge_old_images(retention_days: int) -> int:
    """Remove per-day image folders older than retention_days. Returns count removed."""
    if not retention_days or retention_days <= 0:
        return 0
    root = images_root()
    if not os.path.isdir(root):
        return 0
    cutoff = datetime.now().date() - timedelta(days=int(retention_days))
    removed = 0
    for name in os.listdir(root):
        day_dir = os.path.join(root, name)
        if not os.path.isdir(day_dir):
            continue
        try:
            day = datetime.strptime(name, "%Y-%m-%d").date()
        except ValueError:
            continue  # not a dated folder; leave it alone
        if day < cutoff:
            shutil.rmtree(day_dir, ignore_errors=True)
            removed += 1
            logger.info("Purged old screenshots for %s", name)
    return removed
