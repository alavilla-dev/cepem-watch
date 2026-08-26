from aw_core.config import load_config_toml

default_config = """
[aw-watcher-screenshot]
# Master on/off switch for the screenshot watcher.
enabled = true
# Seconds between capture attempts.
poll_time = 300
# Local-time window during which capture is allowed. Empty = always.
active_hours = "09:00-18:00"
# Comma-separated weekdays when capture is allowed (mon..sun). Empty = all days.
active_days = "mon,tue,wed,thu,fri"
# "all" to capture every monitor, or a 1-based index (e.g. "1").
monitors = "all"
# "jpeg" (smaller) or "png".
image_format = "jpeg"
jpeg_quality = 60
# Downscale images wider than this (px). 0 = keep original size.
max_width = 1920
# Delete stored images older than this many days. 0 = keep forever.
retention_days = 30

[aw-watcher-screenshot-testing]
enabled = true
poll_time = 5
active_hours = ""
active_days = ""
monitors = "all"
image_format = "jpeg"
jpeg_quality = 50
max_width = 1280
retention_days = 1
""".strip()


def load_config(testing: bool):
    section = "aw-watcher-screenshot" + ("-testing" if testing else "")
    return load_config_toml("aw-watcher-screenshot", default_config)[section]
