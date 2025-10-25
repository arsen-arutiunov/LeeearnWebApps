from datetime import datetime
from zoneinfo import ZoneInfo


async def get_now():
    now = datetime.now(ZoneInfo("Europe/Kyiv"))
    print(f"🕜 Час серверу: {now}")
    return now