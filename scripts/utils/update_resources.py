"""Resource Updater

Fetches the Outputs of cloudformation stack and update the resource with its configuration or policy.

Usage
run the script as:
python update_resource.py --prefect-stack-name <prefect stack name> --airbyte-stack-name <airbyte stack name>
                          --s3-bucket <prefect s3 bucket> [--region <aws region>]
"""
import argparse
import os
from time import sleep

import boto3


def _define_arguments():
    """
    Define all the named arguments which are required for script to run
    :return: (object) arguments object
    """
    parser = argparse.ArgumentParser(description='Stores stack outputs in environment')
    parser.add_argument('--airbyte-stack-name', type=str, help='Stack Name', required=True)
    parser.add_argument('--airbyte-policy-path', type=str, help='Path to the file containing policy for Airbyte Stack', required=True)
    parser.add_argument('--region', type=str, help='Region where to create/update stack', default='us-east-1')
    parser.add_argument('--profile', type=str, help='AWS Profile')
    return parser.parse_args()


def _get_resource_from_logical_id(stack_name: str, region: str):
    """
    call the stack and return the stack
    :param stack_name: name of stack
    :param region: where stack is deployed
    :rtype: str
    :return: cloudformation stack
    """
    cloudformation = boto3.resource('cloudformation', region_name=region)
    stack = cloudformation.Stack(stack_name)
    stack_status = [
        'CREATE_IN_PROGRESS', 'DELETE_IN_PROGRESS', 'REVIEW_IN_PROGRESS', 'ROLLBACK_IN_PROGRESS',
        'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_IN_PROGRESS', 'UPDATE_ROLLBACK_IN_PROGRESS',
        'IMPORT_IN_PROGRESS', 'IMPORT_ROLLBACK_IN_PROGRESS'
    ]
    sleep_time = 5
    while stack.stack_status in stack_status:
        sleep(sleep_time)
        stack = cloudformation.Stack(stack_name)
        logging.info(f'current-status:- {stack.stack_status}')
        sleep_time = sleep_time + 5

    if stack.stack_status == 'UPDATE_COMPLETE' or stack.stack_status == 'CREATE_COMPLETE':
        return stack
    return None


def _update_airbyte_stack_policy(stack_name: str, region: str, project_dir: str, policy_path: str):
    """
    Update the airbyte stack policy function
    :param stack_name: cloudformation stack name to update
    :param region: region where lambda is deployed
    :param project_dir: base project path
    """
    with open(os.path.abspath(f'{project_dir}/{policy_path}'),'r') as stack_file:
        json = stack_file.read()
        client = boto3.client('cloudformation', region_name=region)
        client.set_stack_policy(
            StackName=stack_name,
            StackPolicyBody=json
        )
        logging.info('Stack Policy Successfully Uploaded.')


def main():
    args = _define_arguments()
    logging.basicConfig(level=log_level)
    project_dir = ''
    os.chdir(os.path.expanduser("~"))
    for root, dirs, files in os.walk('', topdown=False):
        if root.endswith('prefect-cloudformation'):
            project_dir = root
    if args.profile:
        os.environ['AWS_PROFILE'] = args.profile
    logging.info('Getting stack name')
    airbyte_stack =args.airbyte_stack_name
    airbyte_stack = _get_resource_from_logical_id(args.airbyte_stack_name, args.region)
    if airbyte_stack is None:
        logging.info(f'{args.airbyte_stack_name} already updated')
    else:
        logging.info(f'Updating {args.airbyte_stack_name}')
        _update_airbyte_stack_policy(
            stack_name=args.airbyte_stack_name,
            region=args.region,
            project_dir=project_dir
        )

        logging.info('DONE')
        if args.profile:
            del os.environ['AWS_PROFILE']

    if __name__ == '__main__':
        main()
