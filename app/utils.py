import hashlib
import hmac
import logging
import re
import time

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


def slack_sending_retry(headers: dict) -> bool:
    if headers.get("X-Slack-Retry-Num"):
        return True
    return False


def has_valid_signature(headers: dict, body: dict) -> bool:
    timestamp = headers.get("X-Slack-Request-Timestamp")
    signature = headers.get("X-Slack-Signature")
    if not timestamp or not signature:
        return False

    time_diff = int(time.time()) - int(timestamp)
    if time_diff > 60 * 5:
        return False

    request_body_sig = "v0=" + hmac.new(
        constants.SLACK_SIGNING_SECRET,
        f'v0:{timestamp}:{body}'.encode(),
        hashlib.sha256
    ).hexdigest()
    if signature != request_body_sig:
        return False

    return True


def is_command(command_name: str, text: str):
    if text == command_name or text.startswith(f'{command_name} '):
        return True
    return False
