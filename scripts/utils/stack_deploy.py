import argparse
import json
import os
import time
import logging
import boto3
import botocore.exceptions

from typing import Any, Dict


def _validate_template(template_url: str, client: boto3.client) -> None:
    """
    Read the template file and validate it
    :param template_url: (file) URL of template file on s3
    :param client: (boto3.client) boto3 client
    """
    logging.info(f'Validating template at path: {template_url}')
    client.validate_template(TemplateURL=template_url)


def _parse_parameters(parameters) -> list:
    """
    Reads the parameters file and return the param list
    :param parameters: (file) parameter file to read
    :return: (list) Params list
    """
    if parameters is None:
        return []
    with open(parameters) as parameter_file_obj:
        parameter_data = json.load(parameter_file_obj)
    return parameter_data


def _get_cloudformation_client(region: str) -> boto3.client:
    """
    Creates a cloudformation boto client
    :param region: AWS region
    :return: Cloudformation boto client
    """
    boto3.setup_default_session()
    return boto3.client('cloudformation', region_name=region)


def _get_s3_client(region: str) -> boto3.client:
    """
    Creates a S3 boto client
    :param region: AWS region
    :return: S3 boto client
    """
    return boto3.client('s3', region_name=region)


def _get_s3_url(bucket: str, key: str) -> str:
    """
    Creates an S3 url from bucket name and key
    :param bucket: S3 bucket name
    :param key: S3 key
    :return: S3 object url
    """
    return f'https://{bucket}.s3.amazonaws.com/{key}'


def _upload_file_to_s3(s3_client: boto3.client, bucket: str, key: str, template_path: str) -> str:
    """
    Uploads file to s3 and returns object url
    :param s3_client: S3 boto client
    :param bucket: S3 bucket name
    :param key: S3 key
    :template_path: Path of the template file
    :return: S3 object url
    """
    logging.info(f'Uploading template file: {template_path} to s3 bucket: {bucket}')
    s3_client.upload_file(Filename=template_path, Bucket=bucket, Key=key)
    return _get_s3_url(bucket=bucket, key=key)


def _check_for_stack_existence(client, stack_name):
    logging.info('Checking for stack existence')
    try:
        client.describe_stacks(StackName=stack_name)
        logging.info('Stack exist')
        return True
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Message'].find('does not exist') > -1:
            logging.info('Stack does not exist')
            return False
        raise error


def _describe_change_set(client: boto3.client, stack_name: str, change_set_name: str):
    logging.info('Fetching change-set info')
    change_set_status_retry_count = 0
    response = client.describe_change_set(ChangeSetName=change_set_name, StackName=stack_name)
    while (
            response and response.get('Status', 'FAILED') == 'CREATE_IN_PROGRESS' or
            response.get('Status', 'FAILED') == 'CREATE_PENDING'
    ):
        # Exponential sleep after every describe change set call to prevent throttling
        sleep_duration = ((2 ** change_set_status_retry_count) * 100) # in milliseconds
        time.sleep(sleep_duration / 1000) # sleep function accepts value in seconds
        change_set_status_retry_count += 1

        response = client.describe_change_set(ChangeSetName=change_set_name, StackName=stack_name)
    logging.info('Change-set created successfully')
    return response


def _generate_change_set(
    client: boto3.client, s3_client: boto3.client, stack_name: str, change_set_name: str, template_path: str,
    s3_bucket: str, s3_key: str, parameters: list, stack_exists: bool
) -> Dict[str, Any]:
    """
    Generate the change set for the stack and upload it
    :param client: (object) boto3 cloudformation client
    :param s3_client: (object) s3 cloudformation client
    :param stack_name: (str) name of the stack
    :param change_set_name: (str) change set name
    :param template_path: (str) Path of the template file to create change set for
    :param s3_bucket: (str) S3 bucket name
    :param s3_key: (str) S3 key
    :param parameters: (list) parameters list
    :param stack_exists: (bool) specify whether exist or not
    :return:(dict) dict describing the change set
    """
    if not stack_exists:
        change_set_type = 'CREATE'
    else:
        change_set_type = 'UPDATE'
    try:
        template_url = _upload_file_to_s3(
            s3_client=s3_client,
            template_path=template_path,
            bucket=s3_bucket,
            key=os.path.join(s3_key, os.path.basename(template_path))
        )
        _validate_template(template_url, client)
        logging.info('Generating change-set')
        client.create_change_set(
            StackName=stack_name,
            TemplateURL=template_url,
            ChangeSetName=change_set_name,
            ChangeSetType=change_set_type,
            Parameters=parameters, Capabilities=['CAPABILITY_NAMED_IAM']
        )
    except Exception as e:
        raise e
    return _describe_change_set(client=client, stack_name=stack_name, change_set_name=change_set_name)


def _execute_change_set(client, change_set_name, stack_name):
    logging.info('Applying change-set to stack')
    client.execute_change_set(ChangeSetName=change_set_name, StackName=stack_name)
    response = client.describe_stacks(StackName=stack_name)
    stack = response['Stacks'][0]
    in_progress_stack_status = [
        'CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS', 'REVIEW_IN_PROGRESS',
        'IMPORT_IN_PROGRESS'
    ]
    complete_stack_status = ['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'IMPORT_COMPLETE', ]
    stack_status_retry_count = 1
    while (
            stack and stack.get('StackStatus', 'FAILED') in in_progress_stack_status
    ):
        # Exponential sleep after every describe stack call to prevent throttling
        sleep_duration = 2 ** stack_status_retry_count
        time.sleep(sleep_duration)
        stack_status_retry_count += 1
        response = client.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]
    if stack.get('StackStatus', 'FAILED') in complete_stack_status:
        logging.info('Change-set applied successfully')
        return
    raise Exception(f'Cannot execute change set reason: {response}')


def _get_if_empty_change_set(client, change_set_name, stack_name):
    response = client.describe_change_set(
        ChangeSetName=change_set_name,
        StackName=stack_name
    )
    if len(response['Changes']) == 0:
        return True
    return False


def _define_arguments():
    """
    Define all the named arguments which are required for script to run
    :return: (object) arguments object
    """
    parser = argparse.ArgumentParser(description='Creates or updates the stack')
    parser.add_argument('--stack-name', type=str, help='Stack Name', required=True)
    parser.add_argument('--change-set-name', type=str, help='Change set name', required=True)
    parser.add_argument('--region', type=str, help='Region where to create/update stack', default='us-east-1')
    parser.add_argument('--profile', type=str, help='name of the profile to use')
    parser.add_argument('--template-path', type=str, help='Path to the template file')
    parser.add_argument('--s3-bucket', type=str, help='Name of the s3 bucket to upload template file')
    parser.add_argument('--s3-key', type=str, help='Path in the s3 bucket to upload template file at')
    parser.add_argument('--parameters', type=str, help='Path to parameters file or params list')
    parser.add_argument('--debug', help='Include debug logs', action='store_true')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--no-execute-changeset',
        help='Creates the change-set but does not execute it',
        action='store_true'
    )
    group.add_argument(
        '--only-execute-changeset',
        help='Executes the already created change-set(This argument skips the changeset creation part and '
             'required changeset to be present )',
        action='store_true'
    )
    return parser.parse_args()


def main():
    """
    Main script to create change-set
    """
    args = _define_arguments()
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level)
    if args.profile:
        os.environ['AWS_PROFILE'] = args.profile
    client = _get_cloudformation_client(region=args.region)
    s3_client = _get_s3_client(region=args.region)
    change_set = None
    if args.only_execute_changeset is False:
        stack_exist = _check_for_stack_existence(client=client, stack_name=args.stack_name)
        parameters = _parse_parameters(args.parameters)
        change_set = _generate_change_set(
            client=client,
            s3_client=s3_client,
            stack_name=args.stack_name,
            template_path=args.template_path,
            s3_bucket=args.s3_bucket,
            s3_key=args.s3_key,
            parameters=parameters,
            stack_exists=stack_exist,
            change_set_name=args.change_set_name
        )
    else:
        change_set = _describe_change_set(
            client=client,
            stack_name=args.stack_name,
            change_set_name=args.change_set_name
        )
    if args.no_execute_changeset is False:
        if change_set['Status'] == 'FAILED':
            is_empty = _get_if_empty_change_set(
                client=client,
                change_set_name=args.change_set_name,
                stack_name=args.stack_name
            )
            if is_empty:
                logging.info('Change-set is empty deleting it now')
                client.delete_change_set(ChangeSetName=args.change_set_name, StackName=args.stack_name)
                logging.info('Change-set deleted successfully')
        elif change_set['Status'] == 'CREATE_COMPLETE':
            logging.debug('change-set response:- \n', json.dumps(change_set, default=str, indent=2))
            _execute_change_set(client=client, change_set_name=args.change_set_name, stack_name=args.stack_name)
        else:
            logging.error(change_set)

    if args.profile:
        del os.environ['AWS_PROFILE']


if __name__ == '__main__':
    main()
