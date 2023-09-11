import json
import boto3


def fetch_secrets(secret_arn: str) -> dict:
    """
    Fetch secrets from AWS corresponding to the given arn
    :param secret_arn: ARN of the secret
    :return Secrets dict
    """
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_arn)
    return json.loads(response['SecretString'])


def update_codepipeline_status(action_details: dict) -> dict:
    """
    Update codepipeline status
    :param action_details: action details dict
    :return: approval response dict
    """
    codepipeline_status = "Approved" if action_details["approve"] else "Rejected"
    codepipeline_name = action_details["codepipeline_name"]
    token = action_details["codepipeline_token"]

    client = boto3.client('codepipeline')
    approval_response = client.put_approval_result(
        pipelineName=codepipeline_name,
        stageName='Approval',
        actionName='ManualApproval',
        result={'summary': '', 'status': codepipeline_status},
        token=token)

    return approval_response
