import logging

logger = logging.getLogger("dagi")


def init_logger(loglevel: str = "WARNING") -> None:
    default_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
    )
    default_handler = logging.StreamHandler()
    default_handler.setLevel(loglevel)
    default_handler.setFormatter(default_format)

    logger.addHandler(default_handler)
    logger.setLevel("DEBUG")
