import json
import traceback

import chat_gpt_client
import constants
import utils
from command_clear import ClearCommand
from command_list import ListCommand
from command_set import SetCommand
from errors import CommandParseError, NotImplementedCommandError, UnexpectedError
from response import Response
from slack_client import SlackClient

logger = utils.setup_logger(__name__)


SLACK_MESSAGE_TYPE_APP_MENTION = "app_mention"
SLACK_MESSAGE_TYPE_MESSAGE = "message"

SLACK_MESSAGE_SUB_TYPE_MESSAGE_CHANGED = "message_changed"
SLACK_MESSAGE_SUB_TYPE_MESSAGE_DELETED = "message_deleted"
SLACK_MESSAGE_SUB_TYPE_MESSAGE_TOMBSTONE = "tombstone"


def lambda_handler(event, context):
    slackClient = None
    progress_message_ts = None
    try:
        headers = event.get("headers")

        if utils.slack_sending_retry(headers):
            return Response.success()

        body = event.get("body")
        if not utils.has_valid_signature(headers, body):
            return Response.unauthorized()

        body: dict = json.loads(body)
        body_event: dict = body.get("event")

        logger.info(f"EVENT: {body_event}")

        # 初回Slack認証時
        # if body.get("challenge") is not None:
        #     return Response.success(body.get("challenge"))

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
            return Response.success()
        # DMでユーザがメッセージを削除したとき
        if event_triggered_by_user_message_delete_on_dm(body_event):
            return Response.success()

        user_edited_message = False
        # DMでユーザがメッセージを変更したとき
        if event_triggered_by_user_message_edit_on_dm(body_event):
            text = body_event.get("message").get("text")
            user_edited_message = True
        # チャンネルでユーザがメッセージを変更したとき
        if event_triggered_by_user_message_edit_on_channel(body_event):
            text = body_event.get("text")
            user_edited_message = True

        if not text:
            raise UnexpectedError("Cannot get text")

        sent, text = slackClient.send_error_when_text_is_empty_or_no_mention(
            text)
        if sent:
            return Response.success()

        user_id = body_event.get("user")
        if not user_id:
            message = body_event.get("message")
            if message:
                user_id = message.get("user")

        # セットコマンドの場合
        if utils.is_command("set", text):
            set_command = SetCommand(text, user_id)
            set_command.set_key_value()
            slackClient.send_text_to_channel(
                f"SET {set_command.key}: {set_command.value}"
            )
            return Response.success()
        # リストコマンドの場合
        elif utils.is_command("list", text):
            list_command = ListCommand(text, user_id)
            message = list_command.list_key_value()
            slackClient.send_text_to_channel(message)
            return Response.success()
        # 削除コマンド
        elif utils.is_command("clear", text):
            clear_command = ClearCommand(text, user_id)
            clear_command.clear_value()
            slackClient.send_text_to_channel(
                f"CLEAR {clear_command.key}"
            )
            return Response.success()

        progress_message_ts = slackClient.send_text_to_thread(
            constants.SLACK_PROGRESS_MESSAGE
        )
        replies = None
        if user_edited_message:
            replies = slackClient.thread_replies(text)
        else:
            replies = slackClient.thread_replies()
        response_from_chat_gpt = chat_gpt_client.create_chat_gpt_completion(
            replies,
            user_id
        )

        slackClient.update_sent_text(
            response_from_chat_gpt,
            progress_message_ts,
            user_id
        )

        return Response.success()

    except CommandParseError as e:
        logger.error(traceback.print_exc())
        slackClient.send_text_to_channel(str(e))
        return Response.success()

    except NotImplementedCommandError as e:
        logger.error(traceback.print_exc())
        slackClient.send_text_to_channel(str(e))
        return Response.success()

    except Exception:
        logger.error(traceback.print_exc())
        slackClient.send_text_to_channel("予期しないエラーが発生しちゃいました！ :(")
        if progress_message_ts:
            slackClient.delete_sent_text(progress_message_ts)
        return Response.unexpected("Unexpected error!")


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
    return False
