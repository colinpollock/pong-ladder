from datetime import datetime


def parse_datetime(s):
    """Parse a string into a datetime object.

    The input format should be 'YYYY-MM-DDTHH:MM:SS'.
    """
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')


def now_as_iso_string():
    return format_datetime(now())


def now():
    return datetime.utcnow().replace(microsecond=0)


def format_datetime(dt):
    return dt.isoformat()
