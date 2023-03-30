import os

OPEN_AI_API_KEY = os.environ.get("OPEN_AI_API_KEY")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
DEFAULT_CHAT_GPT_MODEL = "gpt-3.5-turbo"
DEFAULT_CHAT_GPT_MAX_TOKENS = 1000
MAX_REPLIES = 7
CHAT_GPT_SYSTEM_ROLE_CONTENT = """
あなたはAliceです。以下の制約に従って会話してください。
-語尾に"にゃ"を付けて話します。
-Aliceの一人称は"わし"です。
-Aliceは二人称を"あんた"と呼びます。
-Aliceは敬語を使いません。ユーザにフレンドリーに接します。
"""
