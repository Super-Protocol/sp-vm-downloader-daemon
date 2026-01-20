import datetime as dt
import logging
import hashlib
import shutil
import time
import os
from pathlib import Path


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


def ensure_writable_dir(path: str):
    os.makedirs(path, exist_ok=True)
    if not os.access(path, os.W_OK):
        raise PermissionError(f"Directory {path} is not writable")


def remove_directory_full(path_str: str):
    path = Path(path_str)
    if path.is_dir():
        shutil.rmtree(path)


def get_file_sha256(filename: str, chunk_size: int = 100 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()
