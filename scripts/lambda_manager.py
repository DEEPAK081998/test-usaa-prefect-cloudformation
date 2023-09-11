"""Lambda Manager
The Script update the lambda function code or lambda layer

usage: lambda_manager.py [-h] [--stack-name STACK_NAME] [--s3-bucket S3_BUCKET] [--s3-key S3_KEY]
                         (--lambda-ids LAMBDA_IDS [LAMBDA_IDS ...] | --names NAMES [NAMES ...])
                         [--zip-names ZIP_NAMES [ZIP_NAMES ...]] [--region REGION] [--aws-profile AWS_PROFILE]
                         [--req-file-paths REQ_FILE_PATHS [REQ_FILE_PATHS ...]]
                         (--update-lambda | --update-layer | --update-lambda-config)

manage lambda function and layer code

options:
  -h, --help            show this help message and exit
  --stack-name STACK_NAME
                        Stack Name where lambda functions are deployed
  --s3-bucket S3_BUCKET
                        S3 bucket where lambda/layer is deployed
  --s3-key S3_KEY       path in s3 bucket where lambda function or layer code is stored
  --lambda-ids LAMBDA_IDS [LAMBDA_IDS ...]
                        Key names of the output variable holding the lambda function name in stack template
  --names NAMES [NAMES ...]
                        Names of the lambda functions or layers
  --zip-names ZIP_NAMES [ZIP_NAMES ...]
                        zip names of the lambda function or layer deployed on s3 bucket
  --region REGION       Region where to create/update stack
  --aws-profile AWS_PROFILE
                        name of the profile to use
  --req-file-paths REQ_FILE_PATHS [REQ_FILE_PATHS ...]
                        path to the requirements file for which you are uploading layer version
  --update-lambda       updates lambda function code
  --update-layer        updates layer version
  --update-lambda-config
                        updates lambda function configuration
"""
import argparse
import filecmp
import logging
import os
import platform
import re
from time import sleep
from typing import Any, Dict, List, Tuple, Union

import boto3
import git

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('lambda_manager')


def _convert_pascal_case_to_snake_case(input_str: str) -> str:
    """
    Converts PascalCase string to snake_case
    :param input_str: input pascal case string eg. 'PascalCase'
    :return: snake case converted string eg. pascal_case
    """
    return re.sub(r'(?<!^)(?=[A-Z])', '_', input_str).lower()


def _get_lambda_name_from_logical_id(stack_name: str, region: str, lambda_id: str) -> Union[str, None]:
    """
    call the stack and return the lambda function name for the given logical id
    :param stack_name: name of stack
    :param region: where stack is deployed
    :param lambda_id: logical id set in application stack
    :return: lambda function name
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
        print('current-status:-', stack.stack_status)
        sleep_time = sleep_time + 5
    if stack.stack_status in ['UPDATE_COMPLETE', 'CREATE_COMPLETE']:
        lambda_dict = next(output for output in stack.outputs if output['OutputKey'] == lambda_id)
        return lambda_dict['OutputValue']
    return None


def _get_layer_arn_latest_version(client: boto3.client, layer_arn: str) -> str:
    """
    Returns layer arn with latest version
    :param client: lambda boto client
    :param layer_arn: layer arn
    :return: layer arn with latest version
    """
    response = client.list_layer_versions(
        LayerName=layer_arn
    )
    layer_arn = response['LayerVersions'][0]['LayerVersionArn']
    logger.info(f"Found version {response['LayerVersions'][0]['Version']} for layer {layer_arn}")
    return layer_arn


def _remove_layer_version(layer_arn: str) -> str:
    """
    remove layer version from arn
    :param layer_arn: layer arn
    :return: layer arn without version
    """
    return ':'.join(layer_arn.split(':')[:-1])


def _get_layer_arns(client: boto3.client, lambda_name: str) -> List[str]:
    """
    Get latest layer arns
    :param client: lambda boto client
    :param lambda_name: lambda function name
    :return: list of layer arn
    """
    logger.info(f'Getting layers latest version')
    response = client.get_function_configuration(
        FunctionName=lambda_name,
    )
    layer_list = []
    for layer in response.get('Layers', []):
        layer_arn = layer.get('Arn')
        layer_arn = _remove_layer_version(layer_arn)
        layer_arn = _get_layer_arn_latest_version(client=client, layer_arn=layer_arn)
        layer_list.append(layer_arn)
    return layer_list


def _update_lambda(
    lambda_name: str, s3_bucket: str, s3_key: str, region: str, lambda_zip_name: str,
    update_lambda_function_code: bool = True, update_lambda_function_config: bool = False
) -> None:
    """
    Update the lambda function
    :param lambda_name: lambda name to update
    :param s3_bucket: s3 bucket where function is stored
    :param s3_key: s3 key to lambda function
    :param region: region where lambda is deployed
    :param update_lambda_function_code: indicates whether to update lambda code
    :param update_lambda_function_config: indicates whether to update lambda config
    """
    client = boto3.client('lambda', region_name=region)
    if update_lambda_function_code:
        sleep_time = 5
        while sleep_time <= 20:
            try:
                logger.info(f'Updating function code for lambda {lambda_name}')
                client.update_function_code(
                    FunctionName=lambda_name,
                    S3Bucket=s3_bucket,
                    S3Key=f'{s3_key}/{lambda_zip_name}'
                )
                break
            except client.exceptions.ResourceConflictException as e:
                logger.warning(
                    f'Getting error {e} during update for lambda function {lambda_name}, '
                    f'trying again in {sleep_time} seconds'
                )
                sleep(sleep_time)
                sleep_time += 5

    # the only reason for separating this is that lambda update is failing
    if update_lambda_function_config:
        logger.info(f'Updating function configuration for lambda {lambda_name}')
        layer_list = _get_layer_arns(client=client, lambda_name=lambda_name)
        client.update_function_configuration(FunctionName=lambda_name, Layers=layer_list)


def _update_lambda_using_names(
    s3_key: str, region: str, s3_bucket: str, lambda_names: List[str], lambda_zip_names: List[str],
    update_lambda_function_code: bool = True, update_lambda_function_config: bool = False
) -> None:
    """
    Update the lambda functions using the function names
    :param s3_bucket: s3 bucket where function is stored
    :param s3_key: s3 key to lambda function
    :param region: region where lambda is deployed
    :param lambda_names: list of lambda function names
    :param lambda_zip_names: list of lambda function zip names
    :param update_lambda_function_code: indicates whether to update lambda code
    :param update_lambda_function_config: indicates whether to update lambda config
    """
    for index in range(len(lambda_names)):
        lambda_name = lambda_names[index]
        lambda_zip_name = lambda_zip_names[index] if lambda_zip_names else None
        logger.info(f'Updating lambda: {lambda_name} with zip file: {lambda_zip_name}')
        _update_lambda(
            lambda_name=lambda_name,
            s3_bucket=s3_bucket,
            s3_key=s3_key,
            region=region,
            lambda_zip_name=lambda_zip_name,
            update_lambda_function_code=update_lambda_function_code,
            update_lambda_function_config=update_lambda_function_config
        )
        logger.info('DONE')


def _update_lambda_using_logical_ids(
    s3_key: str, region: str, s3_bucket: str, stack_name: str, lambda_ids: List[str], lambda_zip_names: List[str],
    update_lambda_function_code: bool = True, update_lambda_function_config: bool = False
) -> None:
    """
    Update the lambda functions using the lambda resource's logical ids
    :param s3_bucket: s3 bucket where function is stored
    :param s3_key: s3 key to lambda function
    :param region: region where lambda is deployed
    :param stack_name: name of the stack containing lambda function
    :param lambda_ids: list of lambda function resource's logical ids
    :param lambda_zip_names: list of lambda function zip names
    :param update_lambda_function_code: indicates whether to update lambda code
    :param update_lambda_function_config: indicates whether to update lambda config
    """
    for index in range(len(lambda_ids)):
        lambda_name = _get_lambda_name_from_logical_id(stack_name, region, lambda_ids[index])
        if lambda_name is None:
            logger.error(f'Cannot get lambda name for {lambda_ids[index]}')
        else:
            logger.info(f'Updating {lambda_name}')
            _update_lambda(
                lambda_name=lambda_name,
                s3_bucket=s3_bucket,
                s3_key=s3_key,
                region=region,
                lambda_zip_name=lambda_zip_names[index] if lambda_zip_names else None,
                update_lambda_function_code=update_lambda_function_code,
                update_lambda_function_config=update_lambda_function_config
            )
    logger.info('DONE')


def _update_layer_version(s3_bucket: str, s3_key: str, region: str, layer_name: str, layer_zip_name: str) -> None:
    """
    Updates layer to new version
    :param s3_bucket: S3 bucket where layer zip is stored
    :param s3_key: S3 key where layer zip is stored
    :param region: region where layer is deployed
    :param layer_name: layer name
    :param layer_zip_name: layer zip file name
    """
    client = boto3.client('lambda', region_name=region)
    client.publish_layer_version(
        LayerName=layer_name,
        Description='updated layer to latest version',
        Content={
            'S3Bucket': s3_bucket,
            'S3Key': f'{s3_key}/{layer_zip_name}',
        },
        CompatibleRuntimes=[f"python{'.'.join(platform.python_version_tuple()[:-1])}"]
    )


def check_if_identical_txt_files(s3_bucket: str, local_path: str, s3_path: str) -> bool:
    """
    Check if the given txt files are identical on s3 and local file system
    :param s3_bucket: S3 Bucket resource
    :param local_path: Path to the file on local
    :param s3_path: Path to the file on s3
    :return: Boolean result indicating if the text files are identical
    """
    try:
        s3 = boto3.client('s3')
        duplicate_requirement_file_path = '/tmp/requirements.txt'
        s3.download_file(s3_bucket, s3_path, duplicate_requirement_file_path)  # download file to local
        is_identical = filecmp.cmp(local_path, duplicate_requirement_file_path, shallow=False)  # compare files
        if os.path.isfile(duplicate_requirement_file_path):
            os.remove(duplicate_requirement_file_path)
        return is_identical
    except Exception as e:
        logging.error(f'Exception occurred while checking for identical txt files: {e}')
        return False


def _resolve_layer_name(layer_name: str) -> str:
    """
    Resolves layer name or ARN
    :param layer_name: layer name
    :return: return modified arn or name
    """
    if layer_name.startswith('arn'):
        return ':'.join(layer_name.split(':')[:-1])
    return layer_name


def _update_layer_using_names(
    s3_key: str, s3_bucket: str, region: str, layer_names: List[str], layer_zip_names: List[str],
    req_file_path_list: List[str]
) -> None:
    """
    Update the layer version using the layer names
    :param s3_bucket: s3 bucket where layer is stored
    :param s3_key: s3 key to layer code
    :param region: region where layer is deployed
    :param layer_names: list of layers names
    :param layer_zip_names: list of layers zip names
    :param req_file_path_list: list of paths for requirement files
    """
    repo = git.Repo()
    commits_list = list(repo.iter_commits())
    for index in range(len(layer_names)):
        layer_name = _resolve_layer_name(layer_name=layer_names[index])
        layer_zip_name = layer_zip_names[index]
        if check_if_identical_txt_files(
                s3_bucket=s3_bucket,
                local_path=req_file_path_list[index],
                s3_path=f'{s3_key}/{layer_zip_name}'
        ) is False:
            logger.info(f'Updating layer: {layer_name} with zip file: {layer_zip_name}')
            _update_layer_version(
                s3_bucket=s3_bucket,
                s3_key=s3_key,
                region=region,
                layer_name=layer_name,
                layer_zip_name=layer_zip_name
            )
            logger.info('DONE')
        else:
            logger.info(f'Skipped Updating layer {layer_name} because of no change in {req_file_path_list[index]}')


def _get_resource_list_from_stack(stack_name: str, region: str, resource_type: str) -> List[Dict[str, Any]]:
    """
    Get resource list of type from cloudformation stack
    :param stack_name: cloudformation stack name
    :param region: region where layer is deployed
    :param resource_type: type of resource to be fetched eg, 'AWS::Lambda::Function'
    :return: List of resources with given type in the cloudformation stack
    """
    client = boto3.client('cloudformation', region_name=region)
    response = client.list_stack_resources(StackName=stack_name)
    all_resources = response['StackResourceSummaries']
    req_resources = []
    for resource in all_resources:
        if resource['ResourceType'] == resource_type:
            req_resources.append(resource)
    return req_resources


def _get_lambdas_info_from_stack(stack_name: str, region: str) -> Tuple[List[str], List[str]]:
    """
    Get lambda resources info from cloudformation stack
    :param stack_name: cloudformation stack name
    :param region: region where layer is deployed
    :return: lambda names and lambda zip names in a stack
    """
    lambda_resources = _get_resource_list_from_stack(
        stack_name=stack_name,
        region=region,
        resource_type='AWS::Lambda::Function'
    )
    lambda_names = []
    lambda_zip_names = []
    for resource in lambda_resources:
        lambda_zip_name = f"{_convert_pascal_case_to_snake_case(resource['LogicalResourceId'])}.zip"
        lambda_names.append(resource['PhysicalResourceId'])
        lambda_zip_names.append(lambda_zip_name)
    return lambda_names, lambda_zip_names


def _get_info_from_lambda_layer_name(layer_name: str) -> Tuple[str, str]:
    """
    Get requirement file path and layer zip name from layer's logical name
    :param layer_name: s3 bucket where layer is stored
    :return: requirement file path and layer zip name from layer's logical name
    """
    layer_name_snake_case = _convert_pascal_case_to_snake_case(layer_name)
    layer_zip_name = f"{layer_name_snake_case}.zip"
    lambda_dir_name = layer_name_snake_case.removesuffix('_layer')
    requirements_file_path = f'lambdas/{lambda_dir_name}/requirements.txt'
    return requirements_file_path, layer_zip_name


def _get_lambda_layers_info_from_stack(stack_name: str, region: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Get lambda layer resources info from cloudformation stack
    :param stack_name: cloudformation stack name
    :param region: region where layer is deployed
    :return: lambda layer resources info from cloudformation stack
    """
    lambda_layer_resources = _get_resource_list_from_stack(
        stack_name=stack_name,
        region=region,
        resource_type='AWS::Lambda::LayerVersion'
    )
    layer_names = []
    layer_zip_names = []
    requirements_file_paths = []
    for resource in lambda_layer_resources:
        layer_name = resource['LogicalResourceId']
        req_file_path, layer_zip_name = _get_info_from_lambda_layer_name(layer_name=layer_name)
        layer_names.append(layer_name)
        requirements_file_paths.append(req_file_path)
        layer_zip_names.append(layer_zip_name)
    return layer_names, requirements_file_paths, layer_zip_names


def _define_arguments() -> argparse.Namespace:
    """
    Define all the named arguments which are required for script to run
    :return: (object) arguments object
    """
    parser = argparse.ArgumentParser(description='manage lambda function and layer code ')
    group = parser.add_mutually_exclusive_group()
    parser.add_argument('--stack-name', type=str, help='Stack Name where lambda functions are deployed')
    parser.add_argument('--s3-bucket', type=str, help='S3 bucket where lambda/layer is deployed')
    parser.add_argument(
        '--s3-key',
        type=str,
        help='path in s3 bucket where lambda function or layer code is stored'
    )
    group.add_argument(
        '--lambda-ids',
        type=str,
        nargs='+',
        help='Key names of the output variable holding the lambda function name in stack template',
    )
    group.add_argument(
        '--names',
        type=str,
        nargs='+',
        help='Names of the lambda functions or layers',
    )
    parser.add_argument(
        '--zip-names',
        type=str,
        nargs='+',
        help='zip names of the lambda function or layer deployed on s3 bucket'
    )
    parser.add_argument('--region', type=str, help='Region where to create/update stack', default='us-east-1')
    parser.add_argument('--aws-profile', type=str, help='name of the profile to use')
    parser.add_argument(
        '--req-file-paths',
        type=str,
        nargs='+',
        help='path to the requirements file for which you are uploading layer version',
        default=[]
    )
    lambda_layer_selection_group = parser.add_mutually_exclusive_group(required=True)
    lambda_layer_selection_group.add_argument(
        '--update-lambda',
        help='updates lambda function code',
        action='store_true'
    )
    lambda_layer_selection_group.add_argument('--update-layer', help='updates layer version', action='store_true')
    lambda_layer_selection_group.add_argument(
        '--update-lambda-config',
        help='updates lambda function configuration',
        action='store_true'
    )
    return parser.parse_args()


def main():
    args = _define_arguments()
    if args.aws_profile:
        os.environ['AWS_PROFILE'] = args.aws_profile
    if args.update_lambda or args.update_lambda_config:
        if args.names:
            _update_lambda_using_names(
                s3_key=args.s3_key,
                region=args.region,
                s3_bucket=args.s3_bucket,
                lambda_names=args.names,
                lambda_zip_names=args.zip_names,
                update_lambda_function_code=args.update_lambda,
                update_lambda_function_config=args.update_lambda_config
            )
        elif args.lambda_ids:
            _update_lambda_using_logical_ids(
                s3_key=args.s3_key,
                region=args.region,
                s3_bucket=args.s3_bucket,
                stack_name=args.stack_name,
                lambda_ids=args.lambda_ids,
                lambda_zip_names=args.zip_names,
                update_lambda_function_code=args.update_lambda,
                update_lambda_function_config=args.update_lambda_config
            )
        elif args.stack_name:
            lambda_names, lambda_zip_names = _get_lambdas_info_from_stack(
                stack_name=args.stack_name,
                region=args.region
            )
            _update_lambda_using_names(
                s3_key=args.s3_key,
                region=args.region,
                s3_bucket=args.s3_bucket,
                lambda_names=lambda_names,
                lambda_zip_names=lambda_zip_names,
                update_lambda_function_code=args.update_lambda,
                update_lambda_function_config=args.update_lambda_config
            )
    elif args.update_layer:
        if args.names:
            _update_layer_using_names(
                s3_bucket=args.s3_bucket,
                s3_key=args.s3_key,
                region=args.region,
                layer_names=args.names,
                layer_zip_names=args.zip_names,
                req_file_path_list=args.req_file_paths
            )
        elif args.stack_name:
            layer_names, layer_req_file_paths, layer_zip_names = _get_lambda_layers_info_from_stack(
                stack_name=args.stack_name,
                region=args.region
            )
            _update_layer_using_names(
                s3_bucket=args.s3_bucket,
                s3_key=args.s3_key,
                region=args.region,
                layer_names=layer_names,
                layer_zip_names=layer_zip_names,
                req_file_path_list=layer_req_file_paths
            )
    if args.aws_profile:
        del os.environ['AWS_PROFILE']


if __name__ == '__main__':
    main()
