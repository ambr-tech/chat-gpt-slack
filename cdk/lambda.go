package main

import (
	"github.com/aws/aws-cdk-go/awscdk/v2"
	"github.com/aws/aws-cdk-go/awscdk/v2/awsapigateway"
	"github.com/aws/aws-cdk-go/awscdk/v2/awslambda"
	"github.com/aws/aws-cdk-go/awscdk/v2/awsssm"
	"github.com/aws/constructs-go/constructs/v10"
	"github.com/aws/jsii-runtime-go"
)

type LambdaStackProps struct {
	awscdk.StackProps
}

func NewLambdaStack(scope constructs.Construct, id string, props *LambdaStackProps) awscdk.Stack {
	var sprops awscdk.StackProps
	if props != nil {
		sprops = props.StackProps
	}
	stack := awscdk.NewStack(scope, &id, &sprops)

	lambdaFunction := awslambda.NewFunction(stack, jsii.String("ChatGPT_LambdaFunction"), &awslambda.FunctionProps{
		Runtime: awslambda.Runtime_PYTHON_3_7(),
		Code:    awslambda.AssetCode_FromAsset(jsii.String("../app/dist/lambda.zip"), nil),
		Handler: jsii.String("lambda_function.lambda_handler"),
		Environment: &map[string]*string{
			"OPEN_AI_API_KEY": awsssm.StringParameter_ValueForStringParameter(stack, jsii.String("/chat-gpt-slack/OPEN_AI_API_KEY"), nil),
			"SLACK_BOT_TOKEN": awsssm.StringParameter_ValueForStringParameter(stack, jsii.String("/chat-gpt-slack/SLACK_BOT_TOKEN"), nil),
		},
		MemorySize: jsii.Number(256),
		Timeout:    awscdk.Duration_Minutes(jsii.Number(2)),
	})

	apiGateWay := awsapigateway.NewRestApi(stack, jsii.String("ChatGPT_API_Gateway"), &awsapigateway.RestApiProps{
		RestApiName: jsii.String("ChatGPT API Gateway"),
		Description: jsii.String("This service serves chat gpt response"),
	})

	lambdaIntegration := awsapigateway.NewLambdaIntegration(lambdaFunction, &awsapigateway.LambdaIntegrationOptions{
		RequestTemplates: &map[string]*string{
			"application/json": jsii.String("{ \"statusCode\": \"200\"}"),
		},
	})
	apiGateWay.Root().AddMethod(jsii.String("POST"), lambdaIntegration, nil)

	return stack
}

func main() {
	defer jsii.Close()

	app := awscdk.NewApp(nil)

	NewLambdaStack(app, "LambdaStack", &LambdaStackProps{
		awscdk.StackProps{
			Env: nil,
		},
	})

	app.Synth(nil)
}
