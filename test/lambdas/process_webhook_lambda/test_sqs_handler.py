import unittest
import boto3
from moto import mock_sqs
from typing import List

from lambdas.process_webhook_lambda.handlers.sqs_handler import SQSHandler

@mock_sqs
class TestSqsHandler(unittest.TestCase):
    """
    Class to test all functions in sqs_handler.py
    """
    def setUp(self) -> None:
        """
        Test setup
        """
        queue_name = 'test'
        sqs = boto3.resource('sqs')
        self.sqs_client = sqs.create_queue(QueueName=queue_name)
        self.sqs_handler = SQSHandler(queue_name=queue_name)

    def _send_messages(self, messages: List[dict]):
        """
        Send messages to queue
        :param messages: List of messages
        """
        self.sqs_client.send_messages(Entries=messages)

    def _delete_messages(self, messages: List[dict]):
        """
        Delete messages from queue
        :param messages: List of messages
        """
        self.sqs_client.delete_messages(Entries=messages)

    def test_receive_messages(self):
        """
        Test SQS handler receive messages
        """
        messages = [
            {
                'Id': '1',
                'MessageBody': 'abc'
            },
            {
                'Id': '2',
                'MessageBody': 'xyz'
            }
        ]
        self._send_messages(messages=messages)
        response = self.sqs_handler.receive_messages()
        mapped_response = list(map(lambda msg: msg.body, response))
        expected_response = ['abc', 'xyz']
        self.sqs_handler.delete_messages(messages=response)
        self.assertEqual(mapped_response, expected_response)

    def test_delete_messages(self):
        """
        Test SQS handler delete messages
        """
        messages = [
            {
                'Id': '1',
                'MessageBody': 'abc'
            },
            {
                'Id': '2',
                'MessageBody': 'xyz'
            }
        ]
        self._send_messages(messages=messages)
        received_messages = self.sqs_handler.receive_messages()
        self.sqs_handler.delete_messages(messages=received_messages)
        received_messages_after_delete = self.sqs_handler.receive_messages()
        self.assertEqual(len(received_messages_after_delete), 0)
