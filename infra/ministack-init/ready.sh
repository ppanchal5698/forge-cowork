#!/bin/bash
# Runs inside the MiniStack container once services are ready.
# Idempotent: safe to re-run on every container start.

awslocal s3 mb s3://artifacts 2>/dev/null || true

awslocal dynamodb create-table \
  --table-name agent_state \
  --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
  --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST 2>/dev/null || true

DLQ_URL=$(awslocal sqs create-queue --queue-name agent-tasks-dlq --query QueueUrl --output text)
DLQ_ARN=$(awslocal sqs get-queue-attributes --queue-url "$DLQ_URL" \
  --attribute-names QueueArn --query Attributes.QueueArn --output text)
awslocal sqs create-queue --queue-name agent-tasks \
  --attributes "{\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"}"

awslocal sns create-topic --name agent-events

awslocal secretsmanager create-secret --name forge/mcp-api-key --secret-string dummy 2>/dev/null || true
awslocal ssm put-parameter --name /forge/ollama-base-url --value http://ollama:11434 --type String --overwrite

awslocal cognito-idp create-user-pool --pool-name forge-local \
  || echo "WARN: Cognito not available in this MiniStack edition — see CLAUDE.md §7"

echo "MiniStack init complete"
