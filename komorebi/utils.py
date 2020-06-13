import datetime


def parse_dt(dt, naive=True):
    """
    Parse an SQLite datetime, treating it as UTC.
    """
    parsed = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    if naive:
        return parsed
    return parsed.replace(tzinfo=datetime.timezone.utc)


def to_iso_date(dt):
    return parse_dt(dt, naive=False).isoformat()
