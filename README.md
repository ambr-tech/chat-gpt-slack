# chat-gpt-slack

このリポジトリはChatGPTとSlackの連携を行うリポジトリです。

`app`配下にはlambda関数があり、`cdk`配下にはAWSのインフラを構築するCDKがあります。

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

以下コマンドを実行することでデプロイできます。

```sh
/Users/xxx/Desktop/work/chat-gpt-slack

$ AWS_PROFILE=<your_profile> make deploy
```
