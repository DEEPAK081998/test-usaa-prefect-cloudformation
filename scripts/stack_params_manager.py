"""
This script will create/update the paramteres file for a cloudformation stack

Usage: python stack_params_manager.py -p [stack_path]

required arguments:
-p stack_path: stack_path is the relative path of the YAML file containing the stack

"""

import argparse
import json
import logging
import os
import yaml

from cfn_tools.odict import ODict
from cfn_tools import load_yaml


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("update_lambda")


def _create_params_file(file_path: str, stack_parameters: dict) -> None:
    """
    Creates a local parameter file
    :param file_path: path to the local parameters file
    :param stack_parameters: parameters declared inside of the cloudformation stack
    """
    initial_parameters = [
        {"ParameterKey": key, "ParameterValue": ""} for key in stack_parameters
    ]
    with open(file_path, "w") as f:
        logger.info(f"Creating file: {file_path} with {initial_parameters}")
        json.dump(initial_parameters, f, indent=2)


def _update_params_file(file_path: str, stack_parameters: dict) -> None:
    """
    Updates the values of the local parameter file
    :param file_path: path to the local parameters file
    :param stack_parameters: parameters declared inside of the cloudformation stack
    """
    with open(file_path, "r+") as f:
        data = json.load(f)
        initial_params_dict = {key: "" for key in stack_parameters}
        previous_params = {
            item["ParameterKey"]: item["ParameterValue"] for item in data
        }
        for parameter in initial_params_dict:
            initial_params_dict[parameter] = previous_params.get(
                parameter, initial_params_dict[parameter]
            )
        updated_parameters = [
            {"ParameterKey": key, "ParameterValue": value}
            for key, value in initial_params_dict.items()
        ]
        f.seek(0)
        logger.info(f"Updating file: {file_path} with {updated_parameters}")
        json.dump(updated_parameters, f, indent=2)
        f.truncate()


def _load_stack_parameters(path: str) -> ODict:
    """
    Validates the path to cloudformation stack and its content
    :param path: path to the cloud formation stack
    :return: dict containing parameters from the cloudformation stack
    """
    if os.path.exists(path):
        text = open(path).read()
        stack_parameters = load_yaml(text).get("Parameters")
        if stack_parameters is None:
            logger.warning(f"Parameters do not exist in the stack: {path}")
            exit(1)
        return stack_parameters
    else:
        raise Exception(f"Stack {path} Does Not Exists")


def _create_or_update(path: str, stack_parameters: dict) -> None:
    """
    Creates or updates the local parameter file for cloudformation stack
    :param path: path to the cloud formation stack
    :param stack_parameters: parameters declared inside of the cloudformation stack
    """
    dir_path = f"{os.path.dirname(path)}/local"
    file_name = os.path.basename(path).split(".")[0]
    file_path = f"{dir_path}/{file_name}-local-parameters.json"
    if not os.path.exists(dir_path):
        logger.info(f"Creating directory {dir_path}")
        os.mkdir(dir_path)
    if not os.path.exists(file_path):
        _create_params_file(file_path, stack_parameters)
    else:
        _update_params_file(file_path, stack_parameters)


def _define_arguments() -> argparse.Namespace:
    """
    Define all the named arguments which are required for script to run
    :return: (object) arguments object
    """
    parser = argparse.ArgumentParser(description="Creates/Updates Local parameters file for the stack")
    parser.add_argument(
        "-p",
        "--stack_path",
        type=str,
        required=True,
        help="path to the cloud formation stack",
    )
    return parser.parse_args()


def main():
    args = _define_arguments()
    stack_parameters = _load_stack_parameters(path=args.stack_path)
    _create_or_update(path=args.stack_path, stack_parameters=stack_parameters)
    logger.info("DONE")


if __name__ == "__main__":
    main()
