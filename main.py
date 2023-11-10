import sys
from datetime import datetime
import argparse
import logging
import os
import dotenv

ARGS = None
logger = logging.getLogger(__name__)


def set_env():
    env = ARGS.env
    logging.info("Running in %s environment", env)
    dotenv.load_dotenv(dotenv_path=f".env.{env}", override=True)


def config_logger():
    today = datetime.today().strftime("%Y-%m-%d")
    log_file = f"logs/{ARGS.env}-{today}.log"
    if not os.path.exists("logs"):
        os.makedirs("logs")
    if os.path.exists(log_file):
        os.remove(log_file)
    # file_handler = logging.handlers.TimedRotatingFileHandler(
    #     filename=log_file, when="midnight", backupCount=30
    # )
    # file_handler.setLevel(logging.DEBUG)
    # logger.addHandler(file_handler)
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


if __name__ == "__main__":
    ARGS = process_args()
    config_logger()
    set_env()
    from src.app import run

    run()
