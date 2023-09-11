import json
import os
import unittest

import boto3
from moto import mock_s3

from lambdas.dags_management_lambda.constants import *
from lambdas.dags_management_lambda import lambda_handler


@mock_s3
class TestManagementHandler(unittest.TestCase):
    """
    Class to test all functions in dags_management_lambda/lambda_handler.py
    """

    def setUp(self) -> None:
        """
        Test setup
        """
        self.test_bucket_name = 'test_bucket'
        test_dag_file = 'test_template.py'
        self.test_template_path = os.path.join('airflow/dags_template', test_dag_file)
        self.uploaded_template_path = os.path.join(DAGS_S3_PATH, test_dag_file)
        os.environ[S3_BUCKET_KEY_ENV] = self.test_bucket_name
        self._setup_s3_bucket()
        self._setup_events_and_expected_data()

    def tearDown(self) -> None:
        """
        Test teardown
        """
        del os.environ[S3_BUCKET_KEY_ENV]
        os.remove('test_template.py')

    def _validate_s3_file(self) -> None:
        """
        Asserts if the data has been updated in the s3 bucket as expected
        """
        s3_response = self.s3.get_object(Bucket=self.test_bucket_name, Key=self.uploaded_template_path)
        file_contents = json.loads(s3_response['Body'].read().decode().split('=')[-1].replace('\'', '"'))
        self.assertDictEqual(self.expected_data, file_contents)

    def _setup_s3_bucket(self) -> None:
        """
        Creates a s3 bucket and uploads the template file
        """
        self.s3 = boto3.client('s3')
        self.s3_client = self.s3.create_bucket(Bucket=self.test_bucket_name)
        test_dag_file = 'test_template.py'
        fo = open(test_dag_file, 'w')
        fo.write('CONFIG_PARAMS_MAP: dict = {{CONFIG_PARAMS_MAP_PLACEHOLDER}}')
        fo.close()
        self.s3.upload_file(
            test_dag_file,
            os.environ[S3_BUCKET_KEY_ENV],
            self.test_template_path,
        )

    def _setup_events_and_expected_data(self) -> None:
        self.INSERT = 'INSERT'
        self.MODIFY = 'MODIFY'
        self.REMOVE = 'REMOVE'
        self.event_template = {
            'Records': [
                {
                    'eventName': 'INSERT',
                    'dynamodb': {
                        'NewImage': {
                            'dag_name': {'S': 'test_template'},
                            'template_file': {
                                'S': 'airflow/dags_template/test_template.py'
                            },
                        },
                    },
                }
            ]
        }
        self.expected_data = {
            'dag_name': 'test_template',
            'template_file': 'airflow/dags_template/test_template.py',
        }

    def test_new_dag_creation(self) -> None:
        """
        Test creation of new dag upon a valid entry in dynamoDB
        """
        lambda_handler.lambda_handler(self.event_template, None)
        self._validate_s3_file()

    def test_absence_of_template_file(self) -> None:
        """
        Test lambda function when triggered by an event with missing template file
        """
        self.event_template['Records'][0]['dynamodb']['NewImage'].pop('template_file')
        lambda_handler.lambda_handler(self.event_template, None)
        try:
            s3_response = self.s3.get_object(Bucket=self.test_bucket_name, Key=self.uploaded_template_path)
        except Exception as e:
            self.assertEqual(
                e.response['ResponseMetadata']['HTTPStatusCode'], 404)

    def test_removal_of_entry_from_dyanmo_db(self) -> None:
        """
        Test lambda function upon removal of an entry
        """
        lambda_handler.lambda_handler(self.event_template, None)
        self._validate_s3_file()
        self.event_template['Records'][0]['eventName'] = self.REMOVE
        lambda_handler.lambda_handler(self.event_template, None)
        self._validate_s3_file()

    def test_update_of_a_dag(self) -> None:
        """
        Test lambda function upon update of an entry
        """
        lambda_handler.lambda_handler(self.event_template, None)
        self._validate_s3_file()
        self.event_template['Records'][0]['eventName'] = self.MODIFY
        self.event_template['Records'][0]['dynamodb']['NewImage']['dbt_conn_id'] = {'S': 'warehouse'}
        self.expected_data['dbt_conn_id'] = 'warehouse'
        lambda_handler.lambda_handler(self.event_template, None)
        self._validate_s3_file()

    def test_update_of_dag_with_consecutive_insert(self) -> None:
        """
        Test lambda function upon two insert events with same dag_name but different New_Image(s)
        """
        lambda_handler.lambda_handler(self.event_template, None)
        self._validate_s3_file()
        self.event_template['Records'][0]['dynamodb']['NewImage']['dbt_conn_id'] = {'S': 'warehouse'}
        self.expected_data['dbt_conn_id'] = 'warehouse'
        lambda_handler.lambda_handler(self.event_template, None)
        self._validate_s3_file()
