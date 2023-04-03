from dataclasses import asdict, dataclass

import boto3
import constants
import utils

logger = utils.setup_logger(__name__)


@dataclass
class UserConfigItem:
    user_id: str
    system_role_content: str

    def __str__(self) -> str:
        return f'USER_ID: {self.user_id}\nSYSTEM_ROLE_CONTENT: {self.system_role_content}'


class DynamoDBClient:
    def __init__(self):
        dynamodb = boto3.resource('dynamodb')
        self.user_config_table = dynamodb.Table(constants.USER_CONFIG_TABLE)

    def put_item_to_user_config(self, item: UserConfigItem):
        self.user_config_table.put_item(
            Item=asdict(item)
        )
        logger.info(f"PUT Item to USER_CONFIG: {item}")

    def get_item_from_user_config(self, user_id: str) -> UserConfigItem:
        response = self.user_config_table.get_item(
            Key={
                "user_id": user_id
            }
        )
        item = response.get("Item")
        if not item:
            return None
        return UserConfigItem(
            item.get("user_id"),
            item.get("system_role_content")
        )
