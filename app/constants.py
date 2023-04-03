import os

USER_CONFIG_TABLE = os.environ.get("USER_CONFIG_TABLE")
OPEN_AI_API_KEY = os.environ.get("OPEN_AI_API_KEY")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET").encode()
SLACK_PROGRESS_MESSAGE = 'Generating... :ultra-fast-parrot:'
DEFAULT_CHAT_GPT_MODEL = "gpt-3.5-turbo"
DEFAULT_CHAT_GPT_MAX_TOKENS = 1000
MAX_REPLIES = 7
CHAT_GPT_SYSTEM_ROLE_CONTENT = """
""".strip()
# CHAT_GPT_SYSTEM_ROLE_CONTENT = """
# あなたはGPTaroです。以下の制約に従って会話してください。
# -語尾に"にゃ"を付けて話します。
# -GPTaroの一人称は"わし"です。
# -GPTaroは二人称を"あんた"と呼びます。
# -GPTaroは敬語を使いません。ユーザにフレンドリーに接します。
# """

RE_MENTION_PATTERN = r'<@.*?>\s*'
