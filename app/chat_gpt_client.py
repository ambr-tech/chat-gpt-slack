from typing import List

import constants
import openai
import utils
from dynamo_db_client import DynamoDBClient

logger = utils.setup_logger(__name__)


openai.api_key = constants.OPEN_AI_API_KEY


def create_chat_gpt_completion(replies: List[str], user_id: str) -> str:
    messages = []
    if constants.CHAT_GPT_SYSTEM_ROLE_CONTENT != "":
        messages.append(
            {
                "role": "system",
                "content": constants.CHAT_GPT_SYSTEM_ROLE_CONTENT,
            }
        )

    db_client = DynamoDBClient()
    user_config = db_client.get_item_from_user_config(user_id)
    if user_config:
        messages.append(
            {
                "role": "system",
                "content": user_config.system_role_content,
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
