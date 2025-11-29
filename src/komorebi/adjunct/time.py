"""Date/time utilities."""

import datetime


def parse_dt(
    dt: str,
    tz: datetime.tzinfo | None = datetime.UTC,
) -> datetime.datetime:
    """Parse an SQLite datetime, treating it as UTC by default.

    Args:
        dt: an SQLite timestamp string
        tz: the timezone to use, or `None` to treat it naively

    Returns:
        the parsed datetime.
    """
    parsed = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")  # noqa: DTZ007
    return parsed if tz is None else parsed.replace(tzinfo=tz)


def to_iso_date(dt: str, tz: datetime.tzinfo = datetime.UTC) -> str:
    """Convert an SQLite timestamp string to [ISO 8601] format.

    [ISO 8601]: http://en.wikipedia.org/wiki/ISO_8601

    Args:
        dt: an SQLite timestamp string
        tz: a timezone object

    Returns:
        the same timestamp, but in ISO 8601 format.
    """
    return parse_dt(dt, tz).isoformat()


def to_wayback_date(dt: str) -> str:
    return parse_dt(dt).strftime("%Y%m%d%H*")
