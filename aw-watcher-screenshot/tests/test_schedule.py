from datetime import datetime

from aw_watcher_screenshot.schedule import is_active, parse_days, parse_hours


def test_parse_hours():
    assert parse_hours("") is None
    assert parse_hours("bad") is None
    assert parse_hours("09:00-18:00") == (
        __import__("datetime").time(9, 0),
        __import__("datetime").time(18, 0),
    )


def test_parse_days():
    assert parse_days("") is None
    assert parse_days("mon,tue,fri") == {0, 1, 4}
    assert parse_days("garbage") is None


def test_is_active_within_window():
    # Wednesday 2026-08-26, 10:00 -> inside mon-fri / 09-18
    now = datetime(2026, 8, 26, 10, 0)
    assert is_active(now, "09:00-18:00", "mon,tue,wed,thu,fri")


def test_is_active_outside_hours():
    now = datetime(2026, 8, 26, 20, 0)  # 20:00 outside 09-18
    assert not is_active(now, "09:00-18:00", "mon,tue,wed,thu,fri")


def test_is_active_wrong_day():
    now = datetime(2026, 8, 29, 10, 0)  # Saturday
    assert not is_active(now, "09:00-18:00", "mon,tue,wed,thu,fri")


def test_is_active_always_when_unset():
    now = datetime(2026, 8, 29, 3, 0)  # Saturday 03:00
    assert is_active(now, "", "")


def test_overnight_window():
    assert is_active(datetime(2026, 8, 26, 23, 0), "22:00-06:00", "")
    assert is_active(datetime(2026, 8, 26, 5, 0), "22:00-06:00", "")
    assert not is_active(datetime(2026, 8, 26, 12, 0), "22:00-06:00", "")
