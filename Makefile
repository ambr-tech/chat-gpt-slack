.DEFAULT_GOAL := help

.PHONY: help
help: ## Show help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: lint-lambda
lint-lambda: ## Lint lambda
	ruff app/*.py

.PHONY: lint-fix-lambda
lint-fix-lambda: ## Lint fix lambda
	ruff app/*.py --fix

.PHONY: build
build: ## Build lambda function
	cd app && mkdir -p package dist && rm -rf package/* && cp *.py package/ && pip install -r requirements.txt -t ./package/ && cd ./package/ && zip -r ../dist/lambda.zip .

.PHONY: build-ignore-lib
build-ignore-lib: ## Build lambda function, but not re-installing the libraries
	cd app && mkdir -p package dist && cp *.py package/ && cd ./package/ && zip -r ../dist/lambda.zip .

.PHONY: deploy
deploy: ## Deploy using AWS CDK
	cd cdk && cdk deploy
