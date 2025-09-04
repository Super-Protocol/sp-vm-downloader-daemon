import datetime as dt
import time

import logging


def sleep_until_time(time_str: str) -> None:
    hour, minute = map(int, time_str.split(":"))
    now = dt.datetime.now().astimezone()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now > target:
        target += dt.timedelta(days=1)
    sleep_sec = (target - now).total_seconds()
    s = target.strftime("%d-%m-%Y %H-%M %Z")
    logging.info(f"sleeping until {s}")
    time.sleep(sleep_sec)
