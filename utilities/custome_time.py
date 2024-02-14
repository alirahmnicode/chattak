from zoneinfo import ZoneInfo
from datetime import datetime


def get_time():
    database_time = datetime.utcnow()
    database_time
    utc = ZoneInfo("UTC")
    local_tz = ZoneInfo("Asia/Tehran")
    utc_time = database_time.replace(tzinfo=utc)
    localtime = utc_time.astimezone(local_tz)
    return localtime
