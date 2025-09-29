from datetime import datetime, date, time, timezone
import re


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DATETIME_FORMAT2 = "%Y-%m-%dT%H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S.%f"
TIME_FORMAT2 = "%H:%M:%S"


TIMEDELTA_REGEX = re.compile('^(days=(?P<d>\d+),)?(hours=(?P<h>\d+),)?(minutes=(?P<m>\d+),)?seconds=(?P<s>\d+)(\.(?P<ms>\d+))?$')


def stringify_datetime(d: datetime) -> str:
    base = d.strftime(DATETIME_FORMAT2)
    millis = f"{round(d.microsecond / 1000):03d}"
    base = f"{base}.{millis}"
    if d.tzinfo is None or d.tzinfo == timezone.utc:
        return base + "Z"
    else:
        return base + d.strftime("%z")

def stringify_time(d: time) -> str:
    iso = d.strftime(TIME_FORMAT)
    decimal_pos = iso.rfind(".")
    seconds_fraction = iso[decimal_pos + 1:]
    millis = seconds_fraction.rjust(3, "0")[:3]
    return iso[:decimal_pos + 1] + millis

def stringify_date(d: date):
    return d.strftime(DATE_FORMAT)


def parse_datetime_string(s: str) -> datetime:
    try:
        dt = datetime.fromisoformat(s.strip("Z"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            return datetime.strptime(s, DATETIME_FORMAT).replace(tzinfo=timezone.utc)
        except ValueError:
            return datetime.strptime(s, DATETIME_FORMAT2).replace(tzinfo=timezone.utc)


def parse_datetime(d: datetime | date | time | str | float | int) -> datetime:
    if isinstance(d, datetime):
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    if isinstance(d, str):
        return parse_datetime_string(d)
    if isinstance(d, int) or isinstance(d, float):
        return datetime.fromtimestamp(d, tz=timezone.utc)
    if isinstance(d, date):
        return datetime(year=d.year, month=d.month, day=d.day, tzinfo=timezone.utc)
    if isinstance(d, time):
        return datetime(year=datetime.min.year,
                        month=datetime.min.month,
                        day=datetime.min.day,
                        hour=d.hour, minute=d.minute,
                        second=d.second, microsecond=d.microsecond,
                        tzinfo=timezone.utc)
    raise ValueError(f"Unable to smart-parse value as datetime: {d}")


def parse_date_string(s: str) -> date:
    try:
        return datetime.fromisoformat(s.strip("Z")).date()
    except ValueError:
        try:
            return datetime.strptime(s, DATE_FORMAT).date()
        except ValueError:
            return parse_datetime_string(s).date()


def parse_date(d: datetime | date | str | float | int) -> date:
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return parse_date_string(d)
    if isinstance(d, int) or isinstance(d, float):
        return datetime.fromtimestamp(d, tz=timezone.utc).date()
    if isinstance(d, datetime):
        return date(year=d.year, month=d.month, day=d.day)
    raise ValueError(f"Unable to smart-parse value as date: {d}")


def parse_time_string(s: str) -> time:
    try:
        return datetime.fromisoformat(s.strip("Z")).time()
    except ValueError:
        try:
            return datetime.strptime(s, TIME_FORMAT).time()
        except ValueError:
            return datetime.strptime(s, TIME_FORMAT2).time()


def parse_time(t: datetime | time | str | float | int) -> time:
    if isinstance(t, time):
        return t
    if isinstance(t, str):
        return parse_time_string(t)
    if isinstance(t, int) or isinstance(t, float):
        return datetime.fromtimestamp(t, tz=timezone.utc).time()
    if isinstance(t, datetime):
        return t.time()
    raise ValueError(f"Unable to smart-parse value as time: {t}")


def day(dt: datetime) -> datetime:
    return datetime.combine(dt.date(), datetime.min.time())
