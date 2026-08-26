# aw-watcher-screenshot (CEPEM Watch)

Captures the screen on a schedule, **only within configured hours/days**. Images
are stored locally under the CEPEM Watch data dir; each capture also produces an
ActivityWatch event containing the image **path + metadata** (never the image
bytes, so the database stays small).

> **Privacy:** this component records the screen. It is opt-in per the config
> flag and restricted to the configured active window. Make sure users are
> informed and consent before deploying it.

## Config

`[aw-watcher-screenshot]` in `aw-watcher-screenshot.toml`
(`%LOCALAPPDATA%\cepemwatch\cepemwatch\aw-watcher-screenshot\` on Windows):

| Key | Default | Meaning |
|---|---|---|
| `enabled` | `true` | Master on/off switch |
| `poll_time` | `300` | Seconds between captures |
| `active_hours` | `"09:00-18:00"` | Local time window (empty = always) |
| `active_days` | `"mon,tue,wed,thu,fri"` | Weekdays (empty = all) |
| `monitors` | `"all"` | `"all"` or a 1-based index |
| `image_format` | `"jpeg"` | `jpeg` or `png` |
| `jpeg_quality` | `60` | JPEG quality |
| `max_width` | `1920` | Downscale wider images (0 = off) |
| `retention_days` | `30` | Delete images older than this (0 = keep) |

## Storage

- Images: `<data-dir>/aw-watcher-screenshot/images/<YYYY-MM-DD>/<ts>_mon<n>.<ext>`
- Events: bucket `aw-watcher-screenshot_<hostname>`, type `cepem.screenshot`,
  data `{path, monitor, width, height, bytes, format}`.

## Run

```bash
aw-watcher-screenshot            # or: python -m aw_watcher_screenshot
aw-watcher-screenshot --testing  # short interval, no time restriction
```
