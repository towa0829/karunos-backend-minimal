from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

def get_utc_time():
    return datetime.now(tz=timezone.utc)

def get_expires_time(year = 0, month = 3, day = 0, hour = 0, minute = 0, second = 0):
    return get_utc_time() + relativedelta(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second
    )