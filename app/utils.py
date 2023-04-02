import logging
import re

import constants


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler_format = logging.Formatter(
        '[%(levelname)s]: %(asctime)s - %(name)s: %(message)s'
    )
    handler.setFormatter(handler_format)

    logger.addHandler(handler)
    logger.propagate = False

    return logger


def mention_matches(text: str) -> bool:
    if not text:
        return False

    return re.search(constants.RE_MENTION_PATTERN, text)


def remove_mention(text: str) -> str:
    if not text:
        return ""

    return re.sub(constants.RE_MENTION_PATTERN, '', text).strip()
