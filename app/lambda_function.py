import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List

import openai
from constants import *
from slack_sdk import WebClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)


openai.api_key = OPEN_AI_API_KEY

RE_MENTION_PATTERN = r'<@.*?>\s*'


def lambda_handler(event, context):
    slackClient = None
    try:
        headers = event.get("headers")

        if slack_sending_retry(headers):
            return Response.success_response()

        body: dict = json.loads(event.get("body"))
        body_event = body.get("event")

        # 初回Slack認証時
        # if body.get("challenge") is not None:
        #     return Response.success_response(body.get("challenge"))

        # Botによるメッセージ送信だった場合、無視する
        event_triggered_by_bot = body_event.get("bot_id") is not None
        if event_triggered_by_bot:
            return Response.success_response()

        text = body_event.get("text")
        channel = body_event.get("channel")
        thread_ts = body_event.get("thread_ts")
        if thread_ts is None:
            thread_ts = body_event.get("ts")

        slackClient = SlackClient(channel=channel, thread_ts=thread_ts)

        if re.search(RE_MENTION_PATTERN, text):
            text = re.sub(r'<@.*?>\s*', '', text)
            if text == "":
                slackClient.send_text_to_channel("空文字列は処理できません！")
                return Response.success_response()
        else:
            slackClient.send_text_to_channel("メンション付きで送信してください！")
            return Response.success_response()

        replies = slackClient.thread_replies()
        response_from_chat_gpt = create_chat_gpt_completion(replies)
        slackClient.send_text_to_thread(response_from_chat_gpt)

        return Response.success_response()

    except Exception as e:
        logger.error(e)
        slackClient.send_text_to_channel("予期しないエラーが発生しちゃいました！ :(")
        return Response.unexpected_response("Unexpected error!")


def slack_sending_retry(headers: dict) -> bool:
    if headers.get("X-Slack-Retry-Num") is not None:
        return True
    return False


def create_chat_gpt_completion(replies: List[str]) -> str:
    messages = [
        {"role": "system", "content": """
あなたはAliceです。以下の制約に従って会話してください。
-語尾に"にゃ"を付けて話します。
-Aliceの一人称は"わし"です。
-Aliceは二人称を"あんた"と呼びます。
-Aliceは敬語を使いません。ユーザにフレンドリーに接します。
        """}
    ] + replies[-MAX_REPLIES:]

    completion = openai.ChatCompletion.create(
        model=DEFAULT_CHAT_GPT_MODEL,
        messages=messages,
        max_tokens=DEFAULT_CHAT_GPT_MAX_TOKENS
    )

    choices = completion.get("choices")
    if choices is None:
        return "ChatGPT is unavailable to generate completion choices"
    message = choices[0].get("message")
    if message is None:
        return "ChatGPT is unavailable to generate completion message"
    return message.get("content")


@dataclass
class SlackClient:
    channel: str
    thread_ts: str
    client: WebClient = WebClient(SLACK_BOT_TOKEN)

    def thread_replies(self) -> List[Dict]:
        messages: list = self.client.conversations_replies(
            channel=self.channel, ts=self.thread_ts
        ).get("messages")
        texts = []

        for message in messages:
            text = message.get("text")
            # If the message belongs to bot
            if message.get("bot_id") is not None:
                texts.append({"role": "assistant", "content": text})
                continue

            # If user is mentioning
            if re.search(RE_MENTION_PATTERN, text):
                text = re.sub(RE_MENTION_PATTERN, '', text).strip()
                if text != "":
                    texts.append({"role": "user", "content": text})

                continue

        return texts

    def send_text_to_thread(self, text: str):
        self.client.chat_postMessage(
            text=text,
            channel=self.channel,
            thread_ts=self.thread_ts
        )

    def send_text_to_channel(self, text: str):
        self.client.chat_postMessage(
            text=text,
            channel=self.channel
        )


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
    def unexpected_response(message: str = '') -> dict:
        return Response(500, {"message": message}).to_response()
