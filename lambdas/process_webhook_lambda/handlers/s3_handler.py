import boto3
import logging
from typing import Any
from datetime import datetime
from constants import S3_FILE_PATH_FORMAT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('s3_handler')
logger.setLevel(level=logging.INFO)


class S3Handler:
    """
    Handles actions on S3
    """
    def __init__(self, bucket_name: str, region: str = 'us-east-1') -> None:
        """
        :param bucket_name: Name of the s3 bucket
        :param region: AWS region. Default: us-east-1
        """
        self.aws_region = region
        self.bucket_name = bucket_name
        self.s3_client = self._initialize_s3_client()

    def _initialize_s3_client(self) -> Any:
        """
        Initializes S3 client
        :return: S3 client
        """
        session = boto3.Session(region_name=self.aws_region)
        resource = session.resource("s3")
        client = resource.Bucket(self.bucket_name)
        return client

    def _generate_s3_path(self, record_type: str) -> str:
        """
        Generates s3 path for the given record type using the path format defined
        :param record_type: Record type which will be a part of the path
        :return: Formatted s3 path
        """
        current_datetime = datetime.now()
        date = current_datetime.strftime("%d-%m-%y")
        timestamp = str(int(current_datetime.timestamp()))
        return (
            S3_FILE_PATH_FORMAT
            .replace('$RECORD_TYPE', record_type)
            .replace('$DATE', date)
            .replace('$TIMESTAMP', timestamp)
        )

    def upload_csv(self, data: str, record_type: str) -> dict:
        """
        Uploads given csv data to S3 under the given record type
        :param data: CSV data to be uploaded to s3
        :param record_type: Record type under which the csv file will be stored
        :return: S3 upload response dict
        """
        s3_file_path = self._generate_s3_path(record_type=record_type)
        logger.info(f'Uploading csv data to file path: {s3_file_path}')
        return self.s3_client.put_object(
            Key=s3_file_path,
            Body=bytes(data, 'utf-8'),
        )
