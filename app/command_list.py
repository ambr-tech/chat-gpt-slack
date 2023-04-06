from dynamo_db_client import DynamoDBClient, UserConfigItem
from errors import CommandParseError, NotImplementedCommandError

available_list_command_keys = ["user_config"]


class ListCommand:
    def __init__(self, text: str, user_id: str):
        split_text = text.split(" ", 1)
        if len(split_text) < 2:
            raise CommandParseError(
                f"キーを指定してください。\n使用可能なキーは{','.join(available_list_command_keys)}です。"
            )
        self.key = split_text[1].strip()
        self.user_id = user_id
        self.db_client = DynamoDBClient()

    def list_key_value(self) -> str:
        message = ""
        if self.key == "user_config":
            user_config = self.list_user_config()
            if not user_config:
                message = "何も設定されていません"
            else:
                message = str(user_config)

        else:
            raise NotImplementedCommandError(
                f"listコマンドで{self.key}のキーは存在しません\n参照可能なキーは{','.join(available_list_command_keys)}です。"
            )

        return message

    def list_user_config(self) -> UserConfigItem:
        user_config = self.db_client.get_item_from_user_config(self.user_id)
        return user_config
