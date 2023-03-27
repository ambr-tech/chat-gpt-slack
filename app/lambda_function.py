import json
import logging
import re
from dataclasses import dataclass, field

import openai
from constants import *
from slack_sdk import WebClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)


openai.api_key = OPEN_AI_API_KEY


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

        text = re.sub('^<@.*?>', '', body_event.get("text"))
        channel = body_event.get("channel")
        thread_ts = body_event.get("thread_ts")
        if thread_ts is None:
            thread_ts = body_event.get("ts")

        slackClient = SlackClient(channel=channel, thread_ts=thread_ts)
        slackClient.thread_replies()
        response_from_chat_gpt = create_chat_gpt_completion(text)
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


def create_chat_gpt_completion(input_message: str) -> str:
    completion = openai.ChatCompletion.create(
        model=DEFAULT_CHAT_GPT_MODEL, messages=[{"role": "system", "content": """
        あなたはAliceです。以下の制約に従って会話してください。
        - 語尾に"にゃ"を付けて話します。
        - Aliceの一人称は"わし"です。
        - Aliceは二人称を"あんた"と呼びます。
        - Aliceは敬語を使いません。ユーザにフレンドリーに接します。
        """}, {"role": "user", "content": input_message}, ])

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

    def thread_replies(self):
        replies: list = self.client.conversations_replies(
            channel=self.channel, ts=self.thread_ts
        ).get("messages")

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
