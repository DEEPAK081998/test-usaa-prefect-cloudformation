"""
Script ot update the secretmanager value with the given value

Usage:
usage: update_secrets.py [-h] [--stack-name STACK_NAME] [--mappings MAPPINGS]
                         [--aws-profile AWS_PROFILE] [--debug]

Puts the secret value to all the defined secrets

optional arguments:
  -h, --help            show this help message and exit
  --stack-name STACK_NAME
                        AWS secrets cloudformation stack name
  --mappings MAPPINGS   a dict in string form defining key as the logical id
                        of the secrets and value as the value to put in that
                        secret like in form of{"PrefectAPISecret":"api_key"}
  --aws-profile AWS_PROFILE
                        name of the AWS profile to use
  --debug               Include debug logs
"""

import argparse
import json
import logging
import os

import boto3


def _define_arguments() -> argparse.Namespace:
    """
    Define all the named arguments which are required for script to run
    :return: (object) arguments object
    """
    parser = argparse.ArgumentParser(description='Puts the secret value to all the defined secrets')
    parser.add_argument('--stack-name', type=str, help='AWS secrets cloudformation stack name', required=True)
    parser.add_argument(
        '--mappings',
        help='a dict in string form defining key as the logical id of the secrets'
             ' and value as the value to put in that secret like in form of'
             '{"PrefectAPISecret":"api_key"}',
        required=True
    )
    parser.add_argument('--aws-profile', type=str, help='name of the AWS profile to use')
    parser.add_argument('--debug', help='Include debug logs', action='store_true')
    args = parser.parse_args()
    args.mappings = json.loads(args.mappings)
    return args


def _get_cloudformation_client(stack_name: str) -> boto3.resource:
    """
    Fetch and returns the cloudformation stack resource
    :param stack_name: stack name
    :return: stack resource
    """
    logging.info(f'fetching {stack_name} stack resource')
    cloudformation = boto3.resource('cloudformation')
    return cloudformation.Stack(stack_name)


def _fetch_and_process_stack_outputs(stack: boto3.resource) -> dict:
    """
    Travers the secrets stack and return the mapping dict
    :param stack: cloudformation stack
    :return: outputs mapping
    """
    return {output['OutputKey']: output['OutputValue'] for output in stack.outputs}


def _register_all_secret_value(stack_outputs: dict, mappings: dict) -> None:
    """
    process the mapping dict to update the secret manager
    :param stack_outputs: dict containing arn of secretmanager
    :param mappings: dict containing the value to put in secretmanager
    """
    logging.info(f'Registering all secrets')
    client = boto3.client('secretsmanager')
    for key, value in list(mappings.items()):
        if type(value) is dict:
            value = json.dumps(value)
        client.put_secret_value(
            SecretId=stack_outputs[key],
            SecretString=value,
        )
    logging.info(f'Secrets registered successfully')


def main():
    args = _define_arguments()
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level)
    if args.aws_profile:
        os.environ['AWS_PROFILE'] = args.aws_profile
    stack = _get_cloudformation_client(stack_name=args.stack_name)
    stack_output = _fetch_and_process_stack_outputs(stack=stack)
    logging.debug(f'stack output dict: {stack_output}')
    _register_all_secret_value(stack_outputs=stack_output, mappings=args.mappings)
    if args.aws_profile:
        del os.environ['AWS_PROFILE']


if __name__ == '__main__':
    main()
