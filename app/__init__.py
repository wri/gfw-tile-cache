import logging
import os

ENV: str = os.environ["ENV"]


def get_module_logger(name) -> logging.Logger:
    """
    The logger
    """

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(sh)
    if ENV != "production":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger


logger = get_module_logger(__name__)
