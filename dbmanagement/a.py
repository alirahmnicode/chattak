from zoneinfo import ZoneInfo
from datetime import datetime

database_time = datetime.utcnow()
database_time

utc = ZoneInfo("UTC")
localtz = ZoneInfo('Asia/Tehran')

utctime = database_time.replace(tzinfo=utc)
localtime = utctime.astimezone(localtz)
print(localtime)