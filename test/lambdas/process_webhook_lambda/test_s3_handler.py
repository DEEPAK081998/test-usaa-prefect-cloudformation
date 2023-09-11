import unittest
import boto3
from moto import mock_s3

from lambdas.process_webhook_lambda.handlers.s3_handler import S3Handler

@mock_s3
class TestS3Handler(unittest.TestCase):
    """
    Class to test all functions in s3_handler.py
    """
    def setUp(self) -> None:
        """
        Test setup
        """
        bucket_name = 'test'
        s3 = boto3.resource('s3')
        self.s3_client = s3.create_bucket(Bucket=bucket_name)
        self.s3_handler = S3Handler(bucket_name=bucket_name)

    def test_upload_csv(self) -> None:
        """
        Test upload csv with valid string data
        """
        test_data = 'test_data'
        test_record_type = 'test_record_type'
        response = self.s3_handler.upload_csv(data=test_data, record_type=test_record_type)
        s3_object_data = response.get()['Body'].read()
        expected_data = b'test_data'
        expected_bucket_name = self.s3_client.name
        self.assertEqual(s3_object_data, expected_data)
        self.assertEqual(response.bucket_name, expected_bucket_name)
