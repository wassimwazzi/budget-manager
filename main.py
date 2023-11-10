import sys
from datetime import datetime
import argparse
import logging
import os
import dotenv

ARGS = None
root_logger = logging.getLogger()
LOGGER_NAME = "main"
logger = logging.getLogger(LOGGER_NAME)


def set_env():
    env = ARGS.env
    logger.info("Running in %s environment", env)
    dotenv.load_dotenv(dotenv_path=f".env.{env}", override=True)


def config_logger():
    today = datetime.today().strftime("%Y-%m-%d")
    log_file = f"logs/{ARGS.env}-{today}.log"
    if not os.path.exists("logs"):
        os.makedirs("logs")
    if os.path.exists(log_file):
        os.remove(log_file)
    logging.basicConfig(level="DEBUG", filename=log_file)

    if ARGS.verbose:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(ARGS.log_level)
        logger.addHandler(stream_handler)


def process_args():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "-l",
        "--log_level",
        type=str,
        default="INFO",
        help="Set log level. Default is INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument(
        "-e",
        "--env",
        default="dev",
        help="Set environment. Default is dev",
        choices=["dev", "prod"],
    )
    parser.add_argument(
        "-v",
        "--verbose",
        default=True,
        action="store_true",
        help="Print log to stdout. Default is False",
    )
    return parser.parse_args()


def silence_other_loggers():
    # silence loggers from imported modules
    for name in logging.Logger.manager.loggerDict.keys():
        if LOGGER_NAME not in name:
            logging.getLogger(name).setLevel(logging.FATAL)


if __name__ == "__main__":
    ARGS = process_args()
    config_logger()
    set_env()
    from src.app import run

    silence_other_loggers()
    run()
