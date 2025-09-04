#!/usr/bin/env python3

import argparse
import logging
import time

from modules import utils, github, local_storage, storj


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Daemon to automatically download SuperProtocol VM images",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--update-time", help="Update check date and time", default="00:00"
    )
    parser.add_argument(
        "--keep-versions",
        help="How many previous versions should be keeped",
        type=int,
        default=3,
    )
    parser.add_argument("--log-level", help="Log level", default="INFO")
    parser.add_argument(
        "--onetime", help="Run just now not by schedule", action="store_true"
    )
    return parser.parse_args()


def init_logging(level_str: str) -> None:
    level = getattr(logging, level_str.upper(), None)
    if level is None:
        raise Exception(f"wrong log level: {level_str}")
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")


def main():
    args = parseArgs()
    init_logging(args.log_level)

    gh = github.Github()
    ls = local_storage.LocalStorage()
    sj = storj.StorJ()

    while True:
        try:
            latest_github_release = gh.get_latest_release()
            print(latest_github_release)
            # latest_local_release = ls.get_latest_release()

            # if latest_github_release != latest_local_release:
            #    github_release_json = gh.download_release_json(latest_github_release)
            #    temp_release_files = sj.download_release_files(github_release_json)
            #    ls.save_release(temp_release_files)
            #    sj.remove_temp_files(temp_release_files)

            if args.onetime:
                return
            utils.sleep_until_time(args.update_time)
        except Exception as e:
            logging.exception(e)
            time.sleep(60)


if __name__ == "__main__":
    main()
