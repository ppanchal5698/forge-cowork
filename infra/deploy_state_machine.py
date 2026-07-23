"""Build + deploy the "Graph Loop" Step Functions state machine to the configured
endpoint. Idempotent (create or update).

Pattern (CLAUDE.md §6): orchestrator → worker → evaluator, each state a skill Lambda.
Per-state Retry (3x backoff) + Catch route failures to the agent-tasks DLQ (SQS) then
Fail; success publishes to the agent-events SNS topic. ARNs are discovered, not hardcoded.

Local dev deploy — production is Terraform in Sprint 4.
Run: docker compose cp ./infra backend:/infra && docker compose exec backend python /infra/deploy_state_machine.py
"""
import json
import os

import boto3

REGION = os.environ.get("AWS_REGION", "us-east-1")
ENDPOINT = os.environ.get("AWS_ENDPOINT_URL")
NAME = "graph-loop"


def c(service):
    return boto3.client(service, region_name=REGION, endpoint_url=ENDPOINT)


def _lambda_arn(name: str) -> str:
    return c("lambda").get_function(FunctionName=f"skill-{name}")["Configuration"]["FunctionArn"]


def ensure_messaging():
    """Create the orchestrator→worker handoff queue + DLQ (redrive, 3 attempts) and
    the events topic. Idempotent; owned here rather than ready.sh because SQS isn't
    reliably up during MiniStack init."""
    sqs, sns = c("sqs"), c("sns")
    dlq = sqs.create_queue(QueueName="agent-tasks-dlq")["QueueUrl"]
    dlq_arn = sqs.get_queue_attributes(QueueUrl=dlq, AttributeNames=["QueueArn"])[
        "Attributes"
    ]["QueueArn"]
    sqs.create_queue(
        QueueName="agent-tasks",
        Attributes={
            "RedrivePolicy": json.dumps(
                {"deadLetterTargetArn": dlq_arn, "maxReceiveCount": "3"}
            )
        },
    )
    sns.create_topic(Name="agent-events")


def _dlq_url() -> str:
    return c("sqs").get_queue_url(QueueName="agent-tasks-dlq")["QueueUrl"]


def _topic_arn() -> str:
    topics = c("sns").list_topics()["Topics"]
    return next(t["TopicArn"] for t in topics if t["TopicArn"].endswith("agent-events"))


def _role_arn() -> str:
    iam = c("iam")
    try:
        return iam.create_role(
            RoleName="forge-sfn",
            AssumeRolePolicyDocument='{"Version":"2012-10-17","Statement":[]}',
        )["Role"]["Arn"]
    except iam.exceptions.EntityAlreadyExistsException:
        return iam.get_role(RoleName="forge-sfn")["Role"]["Arn"]


def _retry():
    return [{"ErrorEquals": ["States.ALL"], "MaxAttempts": 3, "IntervalSeconds": 1, "BackoffRate": 2.0}]


def _catch():
    return [{"ErrorEquals": ["States.ALL"], "ResultPath": "$.error", "Next": "HandleFailure"}]


def definition() -> str:
    return json.dumps(
        {
            "Comment": "Graph Loop: orchestrator -> worker -> evaluator",
            "StartAt": "Orchestrator",
            "States": {
                # Orchestrator gathers context/research for the task
                "Orchestrator": {
                    "Type": "Task",
                    "Resource": _lambda_arn("research"),
                    "Parameters": {"query.$": "$.title"},
                    "ResultPath": "$.research",
                    "Retry": _retry(),
                    "Catch": _catch(),
                    "Next": "Worker",
                },
                # Worker turns the research into an answer
                "Worker": {
                    "Type": "Task",
                    "Resource": _lambda_arn("summarize"),
                    "Parameters": {"text.$": "$.research.notes"},
                    "ResultPath": "$.worker",
                    "Retry": _retry(),
                    "Catch": _catch(),
                    "Next": "Evaluator",
                },
                # Evaluator judges the answer
                "Evaluator": {
                    "Type": "Task",
                    "Resource": _lambda_arn("evaluate"),
                    "Parameters": {"answer.$": "$.worker.summary", "task.$": "$.title"},
                    "ResultPath": "$.evaluation",
                    "Retry": _retry(),
                    "Catch": _catch(),
                    "Next": "Publish",
                },
                "Publish": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::sns:publish",
                    "Parameters": {"TopicArn": _topic_arn(), "Message.$": "$.worker.summary"},
                    # keep the accumulated state as the execution output; SNS result -> $.publish
                    "ResultPath": "$.publish",
                    "End": True,
                },
                # Failure path: after retries exhaust, park the cause in the DLQ, then Fail
                "HandleFailure": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::sqs:sendMessage",
                    "Parameters": {"QueueUrl": _dlq_url(), "MessageBody.$": "$.error.Cause"},
                    "Next": "Fail",
                },
                "Fail": {"Type": "Fail", "Error": "GraphLoopFailed"},
            },
        }
    )


def deploy() -> str:
    sfn = c("stepfunctions")
    ensure_messaging()
    role = _role_arn()
    defn = definition()
    existing = next(
        (m for m in sfn.list_state_machines()["stateMachines"] if m["name"] == NAME), None
    )
    if existing:
        arn = existing["stateMachineArn"]
        sfn.update_state_machine(stateMachineArn=arn, definition=defn, roleArn=role)
        print(f"updated {arn}")
    else:
        arn = sfn.create_state_machine(name=NAME, definition=defn, roleArn=role)["stateMachineArn"]
        print(f"created {arn}")
    return arn


if __name__ == "__main__":
    deploy()
    print("state machine deployed")
