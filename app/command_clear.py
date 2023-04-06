from dynamo_db_client import DynamoDBClient, UserConfigItem
from errors import CommandParseError, NotImplementedCommandError

available_clear_command_keys = ["system_role_content"]


class ClearCommand:
    def __init__(self, text: str, user_id: str) -> None:
        split_text = text.split(" ", 1)
        if len(split_text) < 2:
            raise CommandParseError(
                f"キーを指定してください。\n使用可能なキーは{','.join(available_clear_command_keys)}です。"
            )
        self.key = split_text[1].strip()
        self.user_id = user_id
        self.db_client = DynamoDBClient()

    def clear_value(self):
        if self.key == "system_role_content":
            self._clear_system_role_content()
        else:
            raise NotImplementedCommandError(
                f'clearコマンドで{self.key}のキーは存在しません\n削除可能なキーはsystem_role_contentです。'
            )

    def _clear_system_role_content(self):
        self.db_client.put_item_to_user_config(
            UserConfigItem(self.user_id, "")
        )
