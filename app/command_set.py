from dynamo_db_client import DynamoDBClient, UserConfigItem
from errors import NotImplementedCommandError


class SetCommand:
    def __init__(self, text: str, user_id: str) -> None:
        split_text = text.split(" ", 2)
        self.key = split_text[1]
        self.value = split_text[2]
        self.user_id = user_id
        self.db_client = DynamoDBClient()

    def set_key_value(self):
        if self.key == "system_role_content":
            self._put_system_role_content()
        else:
            raise NotImplementedCommandError(
                f'setコマンドで{self.key}のキーは存在しません\n設定可能なキーはsystem_role_contentです。'
            )

    def _put_system_role_content(self):
        self.db_client.put_item_to_user_config(
            UserConfigItem(self.user_id, self.value)
        )
