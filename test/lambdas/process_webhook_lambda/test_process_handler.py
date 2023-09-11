import os
import json
import unittest
import boto3
from typing import List
from moto import mock_s3, mock_sqs

from lambdas.process_webhook_lambda.constants import *
from lambdas.process_webhook_lambda.handlers.s3_handler import S3Handler
from lambdas.process_webhook_lambda.handlers.sqs_handler import SQSHandler
from lambdas.process_webhook_lambda.handlers.process_handler import sqs_to_s3_handler

@mock_s3
@mock_sqs
class TestProcessHandler(unittest.TestCase):
    """
    Class to test all functions in process_handler.py
    """
    def setUp(self) -> None:
        """
        Test setup
        """
        test_queue_name = 'test_queue'
        test_bucket_name = 'test_bucket'
        os.environ[ENV_S3_BUCKET_NAME] = test_bucket_name
        os.environ[ENV_WEBHOOKS_QUEUE_NAME] = test_queue_name
        os.environ[ENV_QUEUE_MAX_BATCH_SIZE] = '10'
        os.environ[ENV_QUEUE_MAX_WAIT_TIME] = '10'
        os.environ[ENV_MESSAGES_POLLING_LIMIT] = '10'
        s3 = boto3.resource('s3')
        sqs = boto3.resource('sqs')
        self.s3_client = s3.create_bucket(Bucket=test_bucket_name)
        self.sqs_client = sqs.create_queue(QueueName=test_queue_name)
        self.sqs_handler = SQSHandler(queue_name=test_queue_name)
        self.s3_handler = S3Handler(bucket_name=test_bucket_name)

    def tearDown(self) -> None:
        """
        Test teardown
        """
        del os.environ[ENV_WEBHOOKS_QUEUE_NAME]
        del os.environ[ENV_S3_BUCKET_NAME]

    def _send_messages(self, messages: List[dict]) -> None:
        """
        Send messages to queue
        :param messages: List of messages
        """
        self.sqs_client.send_messages(Entries=messages)

    def test_sqs_to_s3_handler_invalid_msg_body(self) -> None:
        """
        Test receiving invalid msg body from sqs
        """
        messages = [
            {
                'Id': '1',
                'MessageBody': 'invalid_msg_body'
            },
            {
                'Id': '2',
                'MessageBody': 'invalid_msg_body_'
            }
        ]
        self._send_messages(messages=messages)
        try:
            sqs_to_s3_handler()
            assert False
        except json.decoder.JSONDecodeError:
            assert True

    def test_sqs_to_s3_handler_valid_msg_body(self) -> None:
        """
        Test receiving valid message body from sqs
        """
        messages = [
            {
                'Id': '1',
                'MessageBody': '{"name": "abc"}'
            },
            {
                'Id': '2',
                'MessageBody': '{"name": "xyz"}'
            }
        ]
        self._send_messages(messages=messages)
        response = sqs_to_s3_handler()
        s3_objects_iterator = list(self.s3_client.objects.all())
        s3_object = s3_objects_iterator[0]
        s3_object_data = s3_object.get()['Body'].read()
        messages = self.sqs_handler.receive_messages()
        expected_csv_data = b'name\r\nabc\r\nxyz\r\n'
        self.assertEqual(len(s3_objects_iterator), 1)
        self.assertEqual(s3_object_data, expected_csv_data)
        self.assertIsNone(response)
        self.assertEqual(len(messages), 0)
