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


def is_set_command(text: str):
    if text == "set" or text.startswith("set "):
        return True

    return False


def is_list_command(text: str):
    if text == "list" or text.startswith("list "):
        return True

    return False


def is_clear_command(text: str):
    if text == "clear" or text.startswith("clear "):
        return True

    return False


def validate_set_command(text: str) -> Tuple[bool, str]:
    split_text = text.split(" ", 2)
    if len(split_text) < 3:
        return False, "キーまたは設定する値を指定してください。\n設定可能なキーはsystem_role_contentです。"

    return True, None


def validate_list_command(text: str):
    split_text = text.split(" ", 1)
    if len(split_text) < 2:
        return False, "キーを指定してください。\n参照可能なキーはuser_configです。"

    return True, None


def validate_clear_command(text: str):
    split_text = text.split(" ", 1)
    if len(split_text) < 2:
        return False, "キーを指定してください。\n削除可能なキーはsystem_role_contentです。"

    return True, None
