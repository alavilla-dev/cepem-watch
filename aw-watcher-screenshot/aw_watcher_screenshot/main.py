import argparse
import logging
import time as _time
from datetime import datetime, timezone

from aw_client import ActivityWatchClient
from aw_core.log import setup_logging
from aw_core.models import Event

from .capture import capture
from .config import load_config
from .retention import purge_old_images
from .schedule import is_active

logger = logging.getLogger(__name__)

RETENTION_INTERVAL = 3600  # run the purge at most once per hour


def main():
    parser = argparse.ArgumentParser(
        description="Screenshot watcher for CEPEM Watch (captures the screen on a "
        "schedule within configured hours)"
    )
    parser.add_argument("--testing", action="store_true", help="Run in testing mode")
    parser.add_argument("--verbose", action="store_true", help="Be chatty")
    args = parser.parse_args()

    config = load_config(args.testing)
    setup_logging(
        "aw-watcher-screenshot",
        testing=args.testing,
        verbose=args.verbose,
        log_stderr=True,
        log_file=True,
    )

    # PRIVACY: be explicit that this component records the screen.
    logger.info(
        "CEPEM Watch screenshot watcher starting. This captures your screen on a "
        "schedule; images are stored locally. Disable via config "
        "([aw-watcher-screenshot] enabled = false)."
    )

    if not bool(config["enabled"]):
        logger.info("Screenshot watcher is disabled in config; exiting.")
        return

    poll_time = float(config["poll_time"])
    active_hours = str(config["active_hours"])
    active_days = str(config["active_days"])
    monitors = str(config["monitors"])
    image_format = str(config["image_format"])
    jpeg_quality = int(config["jpeg_quality"])
    max_width = int(config["max_width"])
    retention_days = int(config["retention_days"])

    client = ActivityWatchClient("aw-watcher-screenshot", testing=args.testing)
    bucket_id = f"{client.client_name}_{client.client_hostname}"
    client.create_bucket(bucket_id, event_type="cepem.screenshot", queued=True)

    logger.info(
        "Active window: hours=%s days=%s interval=%ss monitors=%s format=%s "
        "retention=%sd",
        active_hours or "always",
        active_days or "all",
        poll_time,
        monitors,
        image_format,
        retention_days,
    )

    last_purge = 0.0
    with client:
        try:
            while True:
                if is_active(datetime.now(), active_hours, active_days):
                    try:
                        shots = capture(
                            monitors,
                            image_format=image_format,
                            jpeg_quality=jpeg_quality,
                            max_width=max_width,
                            now=datetime.now(timezone.utc),
                        )
                        for meta in shots:
                            client.insert_event(
                                bucket_id,
                                Event(
                                    timestamp=datetime.now(timezone.utc),
                                    duration=0,
                                    data=meta,
                                ),
                            )
                        if shots:
                            logger.info("Captured %d screenshot(s)", len(shots))
                    except Exception:
                        logger.exception("Screenshot capture failed")

                if _time.time() - last_purge > RETENTION_INTERVAL:
                    try:
                        purge_old_images(retention_days)
                    except Exception:
                        logger.exception("Retention purge failed")
                    last_purge = _time.time()

                _time.sleep(poll_time)
        except KeyboardInterrupt:
            logger.info("Screenshot watcher stopped")
