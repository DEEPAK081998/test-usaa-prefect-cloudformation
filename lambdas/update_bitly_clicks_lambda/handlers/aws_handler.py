import base64
import boto3
import json
import logging
from botocore.exceptions import ClientError
from typing import Optional, Tuple

import constants


def get_secret(secret_name: str) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Gets secret value from AWS
    :param secret_name: Name of the secret
    :return Tuple with a string and binary secret value
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    session = boto3.session.Session()
    secret_manager_client = session.client(service_name='secretsmanager', region_name='us-east-1')
    try:
        logger.debug('Getting value from secret: %s', secret_name)
        response = secret_manager_client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error('Got an error trying to get secret, error: %s', e.__str__())
        return None, None
    if constants.SECRET_STRING in response:
        secret = response[constants.SECRET_STRING]
        logger.debug('Got ok response with string secret value')
        return json.loads(secret), None
    else:
        decoded_binary_secret = base64.b64decode(response[constants.SECRET_BINARY])
        logger.debug('Got ok response with binary secret value')
        return None, decoded_binary_secret
