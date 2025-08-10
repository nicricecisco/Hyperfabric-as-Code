import logging

def get_logger():
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger(__name__)
    return logger

def log_error_red(logger, message):
    logger.error(f"\033[41m{message}\033[0m")