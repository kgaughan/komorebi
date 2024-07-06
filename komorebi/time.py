import datetime


def parse_dt(
    dt: str,
    tz: datetime.timezone = datetime.timezone.utc,
) -> datetime.datetime:
    """
    Parse an SQLite datetime, treating it as UTC.

    If you want it treated naively, pass `None` as the timezone.
    """
    parsed = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    return parsed if tz is None else parsed.replace(tzinfo=tz)


def to_iso_date(dt: str) -> str:
    return parse_dt(dt).isoformat()


def to_wayback_date(dt: str) -> str:
    return parse_dt(dt).strftime("%Y%m%d%H*")
