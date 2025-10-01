#!/usr/bin/env python3

import argparse
import logging
import signal
import time
import sys

from modules import local_storage, server, github, utils, storj


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Daemon to automatically download SuperProtocol VM images",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--update-time", help="Update check date and time", default="00:00")
    parser.add_argument(
        "--keep-versions",
        help="How many previous versions should be keeped",
        type=int,
        default=3,
    )
    parser.add_argument("--log-level", help="Log level", default="INFO")
    parser.add_argument("--onetime", help="Run just now not by schedule", action="store_true")
    return parser.parse_args()


def init_logging(level_str: str) -> None:
    level = getattr(logging, level_str.upper(), None)
    if level is None:
        raise Exception(f"wrong log level: {level_str}")
    logging.basicConfig(level=level, format="%(asctime)s [%(name)s] [%(levelname)s]: %(message)s")


def main():
    args = parseArgs()
    init_logging(args.log_level)

    gh = github.Github()
    ls = local_storage.LocalStorage(basedir="/var/lib/sp/images")
    sj = storj.StorJ(
        token="1UXqNMwov41q9TgHmyopNg5q2giQ8aTdh1gjKWKjfbWPFrcrnhenp6QZfd5ukyVnYXDx9Cok6RtnQMMnXmoZPrSUMNGZGF9KuLCzvRNmQYHowX14C2xAxtJeH6VCuNX39ist4bRE9L5VT3k41frDVh3cG1gZvsqh4EaDeaJyV6U4xVaqXqULnSb9PozqU97VVLWhfwdnj6XgUM59Wzq7yo7vn8RxwSyn8H74TEiLNGUPPA3frsYZuoqWQkNzbiYev5ByWeLro1TXo7DogD4WALCKfEmpwHs9j9rsX5WZvvZ13ourTiuZp5vTTZkByB2ibxUJqkSoZSpCNVtmDToNVKkMREVySe"
    )
    srv = server.Server("/var/run/sp-vm-downloader.sock", gh, sj, ls)
    srv.run()

    def graceful_shutdown(sig, frame):
        logging.warning(f'recieved signal: `{sig}`')
        srv.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    while True:
        try:
            latest_github_release = gh.get_latest_release()
            latest_local_release = ls.get_latest_release()

            if latest_github_release is not None:
                if latest_github_release != latest_local_release:
                    # first trying to found latest github release locally
                    local_release = ls.get_release(latest_github_release.name)
                    if local_release is not None:
                        ls.save_latest_mark(local_release.name)
                    else:
                        temp_release_dir = sj.download_release_files(latest_github_release)
                        ls.save_release(latest_github_release, temp_release_dir, is_latest=True)

            if args.onetime:
                return
            utils.sleep_until_time(args.update_time)
        except Exception as e:
            logging.exception(e)
            time.sleep(60)


if __name__ == "__main__":
    main()
