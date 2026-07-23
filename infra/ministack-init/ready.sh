#!/bin/bash
# Runs inside the MiniStack container once services are ready (ready.d phase).
# MiniStack injects AWS_ENDPOINT_URL/credentials — the bundled `aws` CLI needs no flags.
# Idempotent: safe to re-run on every container start or /_ministack/reset?init=1.

aws s3 mb s3://artifacts 2>/dev/null || true

aws dynamodb create-table \
  --table-name agent_state \
  --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
  --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST 2>/dev/null || true

DLQ_URL=$(aws sqs create-queue --queue-name agent-tasks-dlq --query QueueUrl --output text)
DLQ_ARN=$(aws sqs get-queue-attributes --queue-url "$DLQ_URL" \
  --attribute-names QueueArn --query Attributes.QueueArn --output text)
aws sqs create-queue --queue-name agent-tasks \
  --attributes "{\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"}"

aws sns create-topic --name agent-events

aws secretsmanager create-secret --name forge/mcp-api-key --secret-string dummy 2>/dev/null || true
aws ssm put-parameter --name /forge/ollama-base-url --value http://ollama:11434 --type String --overwrite

# create-user-pool is not idempotent by name — guard against duplicates on re-run
aws cognito-idp list-user-pools --max-results 10 --query "UserPools[].Name" --output text \
  | grep -q forge-local || aws cognito-idp create-user-pool --pool-name forge-local

echo "MiniStack init complete"
