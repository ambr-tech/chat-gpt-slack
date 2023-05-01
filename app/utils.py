import hashlib
import hmac
import logging
import re
import time
from typing import Tuple

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


def separate_text_with_chunk_size(text: str, chunk_size: int) -> Tuple[str, str]:
    encoded_text = text.encode('utf-8')
    encoded_text_length = len(encoded_text)
    end_position = min(chunk_size, encoded_text_length)
    while end_position < encoded_text_length and encoded_text[end_position] & 0xC0 == 0x80:
        end_position -= 1

    first_chunk = encoded_text[:end_position].decode('utf-8')
    remain_chunk = encoded_text[end_position:].decode('utf-8')

    return first_chunk, remain_chunk
