from dataclasses import dataclass
from typing import Dict, List, Tuple

import constants
import utils
from slack_sdk import WebClient

logger = utils.setup_logger(__name__)


@dataclass
class SlackClient:
    channel: str
    thread_ts: str
    client: WebClient = WebClient(constants.SLACK_BOT_TOKEN)
    thread_messages: list = None

    def __post_init__(self):
        if self.thread_messages is None:
            self.thread_messages = []

    def _append_assistant_role(self, text: str) -> dict:
        return self.thread_messages.append(
            {"role": "assistant", "content": text})

    def _append_user_role(self, text: str) -> dict:
        return self.thread_messages.append({"role": "user", "content": text})

    def thread_replies(self, updated_text: str = None) -> List[Dict]:
        messages: list = self.client.conversations_replies(
            channel=self.channel, ts=self.thread_ts
        ).get("messages")
        logger.info(f'THREAD REPLIES: {messages}')

        for message in messages:
            text = message.get("text")

            # プログレスメッセージは無視する
            if text == constants.SLACK_PROGRESS_MESSAGE:
                continue

            # Botが送信したメッセージの場合
            if message.get("bot_id"):
                text = utils.remove_mention(text)
                self._append_assistant_role(text)
                continue

            # ユーザがメンション指定している場合
            if utils.mention_matches(text):
                text = utils.remove_mention(text)
                if text != "":
                    self._append_user_role(text)

                continue

        # ユーザがメッセージを変更したとき、最新のメッセージとして扱う
        if updated_text:
            self._append_user_role(updated_text)

        return self.thread_messages

    def send_text_to_thread(self, text: str, user_id: str = None) -> str:
        if user_id:
            text = f'<@{user_id}>\n{text}'

        response = self.client.chat_postMessage(
            text=text,
            channel=self.channel,
            thread_ts=self.thread_ts
        )
        return response.data.get("ts")

    def send_text_to_channel(self, text: str):
        self.client.chat_postMessage(
            text=text,
            channel=self.channel
        )

    def update_sent_text(self, text: str, ts: str, user_id: str = None):
        if user_id:
            text = f'<@{user_id}>\n{text}'

        logger.info(f'TEXT: {text}')
        logger.info(f'TEXT_LENGTH: {len(text)}')

        first_text, remain_text = utils.separate_text_with_chunk_size(
            text,
            constants.SLACK_MAX_EDIT_BYTE_SIZE
        )
        self.client.chat_update(
            text=first_text,
            channel=self.channel,
            ts=ts
        )
        if remain_text:
            self.send_text_to_thread(remain_text, user_id)

    def delete_sent_text(self, ts: str):
        self.client.chat_delete(
            channel=self.channel,
            ts=ts
        )

    def send_error_when_text_is_empty_or_no_mention(
            self, text: str) -> Tuple[bool, str]:
        if utils.mention_matches(text):
            text = utils.remove_mention(text)
            if text == "":
                self.send_text_to_channel("空文字は処理できません！")
                return True, None
        else:
            self.send_text_to_channel("メンション付きで送信してください")
            return True, None

        return False, text
