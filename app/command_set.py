from dynamo_db_client import DynamoDBClient, UserConfigItem
from errors import CommandParseError, NotImplementedCommandError

available_set_command_keys = ["system_role_content"]


class SetCommand:
    def __init__(self, text: str, user_id: str):
        split_text = text.split(" ", 2)
        if len(split_text) < 3:
            raise CommandParseError(
                f"キーまたは設定する値を指定してください。\n使用可能なキーは{','.join(available_set_command_keys)}です。"
            )

        self.key = split_text[1].strip()
        self.value = split_text[2].strip()
        self.user_id = user_id
        self.db_client = DynamoDBClient()

    def set_key_value(self):
        if self.key == "system_role_content":
            self._put_system_role_content()
        else:
            raise NotImplementedCommandError(
                f"setコマンドで{self.key}のキーは使用できません\n使用可能なキーは{','.join(available_set_command_keys)}です。"
            )

    def _put_system_role_content(self):
        self.db_client.put_item_to_user_config(
            UserConfigItem(self.user_id, self.value)
        )
