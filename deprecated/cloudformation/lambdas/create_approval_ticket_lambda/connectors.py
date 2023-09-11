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
