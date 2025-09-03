#!/usr/bin/env python3

import argparse
import logging

from modules import utils

def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Daemon to automatically download SuperProtocol VM images",
    )
    parser.add_argument("--update-time", help="Update check date and time", default="00:00")
    parser.add_argument("--keep-versions", help="How many previous versions should be keeped", type=int, default=3)
    parser.add_argument("--log-level", help="Log level", default="INFO")
    parser.add_argument("--onetime", help="Run just now not by schedule", action="store_true")
    return parser.parse_args()

def init_logging(level_str: str) -> None:
    level = getattr(logging, level_str.upper(), None)
    if level is None:
        raise Exception(f"wrong log level: {level_str}")
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")

def main():
    args = parseArgs()
    init_logging(args.log_level)
    while True:
        print(args)
        if args.onetime:
            return
        utils.sleep_until_time(args.update_time)

if __name__ == '__main__':
    main()
