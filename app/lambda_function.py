import hashlib
import hmac
import json
import time
import traceback
from dataclasses import dataclass
from typing import List

import constants
import openai
import utils
from slack_client import SlackClient

logger = utils.setup_logger(__name__)


openai.api_key = constants.OPEN_AI_API_KEY

SLACK_MESSAGE_TYPE_APP_MENTION = "app_mention"
SLACK_MESSAGE_TYPE_MESSAGE = "message"

SLACK_MESSAGE_SUB_TYPE_MESSAGE_CHANGED = "message_changed"
SLACK_MESSAGE_SUB_TYPE_MESSAGE_DELETED = "message_deleted"
SLACK_MESSAGE_SUB_TYPE_MESSAGE_TOMBSTONE = "tombstone"


class UnexpectedError(Exception):
    pass


def lambda_handler(event, context):
    slackClient = None
    progress_message_ts = None
    try:
        headers = event.get("headers")

        if slack_sending_retry(headers):
            return Response.success_response()

        body = event.get("body")
        if not has_valid_signature(headers, body):
            return Response.unauthorized_response()

        body: dict = json.loads(body)
        body_event: dict = body.get("event")

        logger.info(f"EVENT: {body_event}")

        # 初回Slack認証時
        # if body.get("challenge") is not None:
        #     return Response.success_response(body.get("challenge"))

        text = body_event.get("text")
        channel = body_event.get("channel")
        thread_ts = body_event.get("thread_ts")
        if not thread_ts:
            message = body_event.get("message")
            if message:
                thread_ts = message.get("thread_ts")
            else:
                thread_ts = body_event.get("ts")

        slackClient = SlackClient(channel=channel, thread_ts=thread_ts)

        # DMでBotから送信されたメッセージは無視する
        if event_triggered_by_bot(body_event):
            return Response.success_response()
        # DMでユーザがメッセージを削除したとき
        if event_triggered_by_user_message_delete_on_dm(body_event):
            return Response.success_response()

        updated_text = None
        # DMでユーザがメッセージを変更したとき
        if event_triggered_by_user_message_edit_on_dm(body_event):
            updated_text = body_event.get("message").get("text")
        # チャンネルでユーザがメッセージを変更したとき
        if event_triggered_by_user_message_edit_on_channel(body_event):
            updated_text = body_event.get("text")

        if text:
            sent, text = slackClient.send_error_when_text_is_empty_or_no_mention(
                text)
            if sent:
                return Response.success_response()
        elif updated_text:
            sent, updated_text = slackClient.send_error_when_text_is_empty_or_no_mention(
                updated_text)
            if sent:
                return Response.success_response()
        else:
            raise UnexpectedError("Cannot get text nor updated_text")

        progress_message_ts = slackClient.send_text_to_thread(
            constants.SLACK_PROGRESS_MESSAGE
        )
        replies = slackClient.thread_replies(updated_text)
        response_from_chat_gpt = create_chat_gpt_completion(replies)

        user_id = body_event.get("user")
        if not user_id:
            message = body_event.get("message")
            if message:
                user_id = message.get("user")
        slackClient.update_sent_text(
            response_from_chat_gpt,
            progress_message_ts,
            user_id
        )

        return Response.success_response()

    except Exception:
        logger.error(traceback.print_exc())
        slackClient.send_text_to_channel("予期しないエラーが発生しちゃいました！ :(")
        if progress_message_ts:
            slackClient.delete_sent_text(progress_message_ts)
        return Response.unexpected_response("Unexpected error!")


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


def create_chat_gpt_completion(replies: List[str]) -> str:
    messages = []
    if constants.CHAT_GPT_SYSTEM_ROLE_CONTENT != "":
        messages.append(
            {
                "role": "system",
                "content": constants.CHAT_GPT_SYSTEM_ROLE_CONTENT,
            }
        )
    messages.extend(replies[-constants.MAX_REPLIES:])
    logger.info(f"Messages sent to ChatGPT: {messages}")

    completion = openai.ChatCompletion.create(
        model=constants.DEFAULT_CHAT_GPT_MODEL,
        messages=messages,
        max_tokens=constants.DEFAULT_CHAT_GPT_MAX_TOKENS
    )

    return completion.get("choices")[0].get("message").get("content")


@dataclass(frozen=True)
class Response:
    status_code: int
    body: dict

    def to_response(self) -> dict:
        return {
            "headers": {
                "Content-Type": "application/json",
            },
            "statusCode": self.status_code,
            "body": json.dumps(self.body)
        }

    @staticmethod
    def success_response(message: str = '') -> dict:
        return Response(200, {"message": message}).to_response()

    @staticmethod
    def unauthorized_response(message: str = '') -> dict:
        return Response(401, {"message": message}).to_response()

    @staticmethod
    def unexpected_response(message: str = '') -> dict:
        return Response(500, {"message": message}).to_response()


def event_triggered_by_bot(body_event: dict) -> bool:
    # Botによるメッセージ送信がトリガーとなったとき
    bot_id = body_event.get("bot_id")
    if bot_id:
        return True

    subtype = body_event.get("subtype")

    # Botによるメッセージ変更、削除がトリガーとなったとき
    if subtype in [
            SLACK_MESSAGE_SUB_TYPE_MESSAGE_CHANGED,
            SLACK_MESSAGE_SUB_TYPE_MESSAGE_DELETED
    ]:
        message = body_event.get("message")
        if message:
            bot_id = message.get("bot_id")
            if bot_id:
                return True

    return False


def event_triggered_by_user_message_edit_on_dm(body_event: dict) -> bool:
    subtype = body_event.get("subtype")

    if subtype == SLACK_MESSAGE_SUB_TYPE_MESSAGE_CHANGED:
        message = body_event.get("message")
        if message:
            client_msg_id = message.get("client_msg_id")
            if client_msg_id:
                return True

    return False


def event_triggered_by_user_message_delete_on_dm(body_event: dict) -> bool:
    subtype = body_event.get("subtype")

    if subtype == SLACK_MESSAGE_SUB_TYPE_MESSAGE_DELETED:
        previous_message = body_event.get("previous_message")
        if previous_message:
            client_msg_id = previous_message.get("client_msg_id")
            if client_msg_id:
                return True

    # メッセージが削除された後に、削除したメッセージがSlackBotの投稿に変わってイベントが発生してしまう
    if subtype == SLACK_MESSAGE_SUB_TYPE_MESSAGE_CHANGED:
        message = body_event.get("message")
        if message:
            message_subtype = message.get("subtype")
            if message_subtype == SLACK_MESSAGE_SUB_TYPE_MESSAGE_TOMBSTONE:
                return True

    return False


def event_triggered_by_user_message_edit_on_channel(body_event: dict) -> bool:
    client_msg_id = body_event.get("client_msg_id")
    if client_msg_id:
        edited = body_event.get("edited")
        if edited:
            return True

    return False
