"""Active-window helpers: decide whether capturing is allowed right now."""
from datetime import datetime, time
from typing import Optional, Tuple

_DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def parse_hours(active_hours: str) -> Optional[Tuple[time, time]]:
    """Parse "HH:MM-HH:MM" -> (start, end). Empty/invalid -> None (always active)."""
    s = (active_hours or "").strip()
    if not s:
        return None
    try:
        start_s, end_s = s.split("-", 1)
        sh, sm = (int(x) for x in start_s.strip().split(":"))
        eh, em = (int(x) for x in end_s.strip().split(":"))
        return time(sh, sm), time(eh, em)
    except (ValueError, TypeError):
        return None


def parse_days(active_days: str) -> Optional[set]:
    """Parse "mon,tue,..." -> set of weekday indices (0=mon). Empty -> None (all days)."""
    s = (active_days or "").strip().lower()
    if not s:
        return None
    days = set()
    for tok in s.split(","):
        tok = tok.strip()[:3]
        if tok in _DAYS:
            days.add(_DAYS.index(tok))
    return days or None


def _in_hours(now_t: time, window: Tuple[time, time]) -> bool:
    start, end = window
    if start <= end:
        return start <= now_t <= end
    # Overnight window (e.g. 22:00-06:00)
    return now_t >= start or now_t <= end


def is_active(now: datetime, active_hours: str, active_days: str) -> bool:
    """True if `now` (local) falls within the configured days and hours."""
    days = parse_days(active_days)
    if days is not None and now.weekday() not in days:
        return False
    window = parse_hours(active_hours)
    if window is not None and not _in_hours(now.time(), window):
        return False
    return True
