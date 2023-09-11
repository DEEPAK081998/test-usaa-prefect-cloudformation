import fileinput
import logging
import os

import boto3
from dynamodb_json import json_util

import constants

logging.basicConfig(level=logging.INFO)


class DagsManager:
    def __init__(self) -> None:
        """
        Initializes Dags Manager class
        """
        self.logger = logging.getLogger('dags_manager_logs')
        self.logger.setLevel(level=logging.INFO)
        self.s3_client = boto3.client('s3')
        self.dag_name_key = os.environ.get(constants.DAG_NAME_KEY_ENV, constants.DAG_NAME)
        self.template_file_key = os.environ.get(constants.TEMPLATE_FILE_KEY_ENV, constants.TEMPLATE_FILE)
        # not using get() here as this key is mandatory otherwise we need our function to fail
        self.s3_bucket = os.environ[constants.S3_BUCKET_KEY_ENV]
        self.dags_s3_path = os.environ.get(constants.DAGS_S3_PATH_KEY_ENV, constants.DAGS_S3_PATH)

    def _create_or_update_dag(self, config: dict) -> None:
        """
        Function to creates or update dags from config
        :param config: dag config containing dags params and info about dynamic dag file
        """
        json_config = json_util.loads(config)
        dag_name = json_config[self.dag_name_key]
        dag_template_path = json_config.get(self.template_file_key)
        self.logger.info(f'Processing dag {dag_name}')

        if not dag_template_path:
            self.logger.warning(
                f'not able to find {self.template_file_key} key in {dag_name} skipping creation or updation of dag'
            )
            return

        file_name = f'{dag_name}.py'
        destination_path = os.path.join(constants.TMP_PATH, file_name)
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        self.s3_client.download_file(self.s3_bucket, dag_template_path, destination_path)

        for line in fileinput.input(destination_path, inplace=True):
            print(line.replace(constants.CONFIG_PARAMS_MAP_PLACEHOLDER, f'{json_config}'), end='')

        s3_dag_path = os.path.join(self.dags_s3_path, file_name)
        self.s3_client.upload_file(destination_path, self.s3_bucket, s3_dag_path)
        self.logger.info(f'dynamic dag uploaded successfully to bucket s3://{self.s3_bucket}/{s3_dag_path}')

    def manage_dag(self, record: dict) -> None:
        """
        Main function to manage dags
        :param record: event records containing event source data
        """
        if record[constants.EVENT_NAME] in [constants.INSERT, constants.MODIFY]:
            self._create_or_update_dag(config=record[constants.DYNAMO_DB][constants.NEW_IMAGE])
