# chat-gpt-slack

[![FOSSA Status](https://app.fossa.com/api/projects/custom%2B37611%2Fchat-gpt-slack.svg?type=small)](https://app.fossa.com/projects/custom%2B37611%2Fchat-gpt-slack?ref=badge_small)

This repository integrates ChatGPT with Slack.

The `app` directory contains Lambda functions, and the `cdk` directory includes the AWS Cloud Development Kit (CDK) for building AWS infrastructure.

## Lint

Use [Ruff](https://github.com/charliermarsh/ruff) to check Python code.

```sh
$ make lint-lambda
```

## Building Lambda

> **Note**
> When cloning for the first time, always run the following command to generate a Zip file. CDK deployment will fail if the Zip file is missing.

If you modify `requirements.txt` or `lambda_function.py`, run the following command to generate a Zip file.

```sh
$ pwd
/Users/xxx/Desktop/work/chat-gpt-slack

# Execute the following when you add or remove libraries
$ make build

# Execute the following if you did not add the library
$ make build-ignore-lib
```

## Deployment

### Setting Credentials

Before deploying CDK, you need to configure credentials in the AWS Systems Manager Parameter Store.
Run the following commands to save each credential.

- `OPEN_AI_API_KEY`
  - Get the API key from the OpenAI website.
- `SLACK_BOT_TOKEN`
  - Get the `Bot User OAuth Token` from the `OAuth & Permissions` in the side menu of the SlackAPI website.
- `SLACK_SIGNING_SECRET`
  - Get the `Signing Secret` from the `AppCredentials` in the `Basic Information` in the side menu of the SlackAPI website.

```sh
aws ssm put-parameter --name "/chat-gpt-slack/OPEN_AI_API_KEY" --value <OPEN_AI_API_KEY> --type "String"
aws ssm put-parameter --name "/chat-gpt-slack/SLACK_BOT_TOKEN" --value <SLACK_BOT_TOKEN> --type "String"
aws ssm put-parameter --name "/chat-gpt-slack/SLACK_SIGNING_SECRET" --value <SLACK_SIGNING_SECRET> --type "String"
```

### Deploying to AWS

You can deploy using the following command.

```sh
$ pwd
/Users/xxx/Desktop/work/chat-gpt-slack

$ AWS_PROFILE=<your_profile> make deploy
```

## LICENSE

This project is licensed under the MIT License.

[![FOSSA Status](https://app.fossa.com/api/projects/custom%2B37611%2Fchat-gpt-slack.svg?type=large)](https://app.fossa.com/projects/custom%2B37611%2Fchat-gpt-slack?ref=badge_large)
