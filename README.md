# chat-gpt-slack

このリポジトリはChatGPTとSlackの連携を行うリポジトリです。

`app`配下にはlambda関数があり、`cdk`配下にはAWSのインフラを構築するCDKがあります。

## Lint

[Ruff](https://github.com/charliermarsh/ruff)を利用してPythonコードをチェックする。

```sh
$ make lint-lambda
```

## Lambdaのビルド

> **Note**
> 初回クローン時は必ず以下コマンドを実行してZipファイルを生成してください。ZipファイルがないことからCDKのデプロイが失敗します。

`requirements.txt`または`lambda_function.py`を変更した場合は、以下コマンドを実行してZipファイルを生成してください。

```sh
$ pwd
/Users/xxx/Desktop/work/chat-gpt-slack

# ライブラリを追加、削除している場合は以下を実行
$ make build

# ライブラリを追加、削除していない場合は以下を実行
$ make build-ignore-lib
```

## デプロイ

### Credentialの設定

CDKのデプロイ前に、AWS Systems ManagerのパラメータストアにCredentialの設定をする必要があります。

以下コマンドを実行して各Credentialを保存してください。

- `OPEN_AI_API_KEY`
  - OpenAIのサイトからAPIキーを発行してください。
- `SLACK_BOT_TOKEN`
  - SlackAPIのサイトのサイドメニューにある`OAuth & Permissions`から`Bot User OAuth Token`を取得してください。
- `SLACK_SIGNING_SECRET`
  - SlackAPIのサイトのサイドメニューにある`Basic Information`から`AppCredentials`にある`Signing Secret`を取得してください。

```sh
aws ssm put-parameter --name "/chat-gpt-slack/OPEN_AI_API_KEY" --value <OPEN_AI_API_KEY> --type "String"
aws ssm put-parameter --name "/chat-gpt-slack/SLACK_BOT_TOKEN" --value <SLACK_BOT_TOKEN> --type "String"
aws ssm put-parameter --name "/chat-gpt-slack/SLACK_SIGNING_SECRET" --value <SLACK_SIGNING_SECRET> --type "String"
```

### AWSへのデプロイ

以下コマンドを実行することでデプロイできます。

```sh
$ pwd
/Users/xxx/Desktop/work/chat-gpt-slack

$ AWS_PROFILE=<your_profile> make deploy
```
