import boto3
import logging
from typing import List, Any
from botocore.exceptions import ClientError
from constants import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('sqs_handler')
logger.setLevel(level=logging.INFO)


class SQSHandler:
    """
    Handles actions on SQS
    """
    def __init__(self,
        queue_name: str,
        region: str = 'us-east-1',
        max_wait_time: int = None,
        max_batch_size: int = None,
        messages_polling_limit: int = MESSAGES_POLLING_LIMIT_DEFAULT
    ) -> None:
        """
        :param queue_name: Name of the sqs queue
        :param region: AWS region
        :param max_wait_time: Time to wait before receiving an empty response (in seconds)
        :param max_batch_size: Maximum amount of messages to be returned in a single receive request
        :param messages_polling_limit: Maximum amount of messages to be processed across all requests
        """
        self.aws_region = region
        self.queue_name = queue_name
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.messages_polling_limit = messages_polling_limit
        self.sqs_client = self._initialize_sqs_client()

    def _initialize_sqs_client(self) -> Any:
        """
        Initializes SQS client
        :return: SQS client
        """
        session = boto3.Session(region_name=self.aws_region)
        resource = session.resource("sqs")
        client = resource.get_queue_by_name(QueueName=self.queue_name)
        return client

    def _receive_message_batch(self) -> List[dict]:
        """
        Receives a message batch
        :return: List of SQS message objects
        """
        kwargs = {}
        if self.max_batch_size:
            kwargs['MaxNumberOfMessages'] = self.max_batch_size
        if self.max_wait_time:
            kwargs['WaitTimeSeconds'] = self.max_wait_time
        return self.sqs_client.receive_messages(**kwargs)

    def _delete_message_batch(self, message_batch: List[dict]) -> dict:
        """
        Deletes a message batch
        :param message_batch: Batch of messages to delete from queue
        :return: SQS delete message batch response dict
        """
        formatted_message_batch = [
            {'Id': str(i+1), 'ReceiptHandle': message_batch[i].receipt_handle} for i in range(len(message_batch))
        ]
        return self.sqs_client.delete_messages(Entries=formatted_message_batch)

    def receive_messages(self) -> List[dict]:
        """
        Receive messages from SQS till polling limit is reached
        :return: List of SQS messages objects
        """
        messages = []
        while len(messages) < self.messages_polling_limit:
            logger.info("Beginning message poll")
            try:
                message_batch = self._receive_message_batch()
                if not message_batch:
                    logger.info("No messages recieved during poll, time out reached")
                    break
                messages += message_batch
            except ClientError as error:
                raise Exception("Error in AWS Client: " + str(error))
        logger.info(f'Total messages received: {len(messages)}')
        return messages

    def delete_messages(self, messages: List[dict]) -> None:
        """
        Deletes given messages from the SQS queue
        :param messages: List of SQS message objects
        """
        logger.info('Beginning messages delete')
        batch_size = self.max_batch_size or DELETE_BATCH_SIZE_DEFAULT
        for i in range(0, len(messages), batch_size):
            logger.info(f'Deleting messages from batch index {i} to {i + batch_size}')
            message_batch = messages[i:i + batch_size]
            self._delete_message_batch(message_batch=message_batch)
        logger.info(f'Successfully deleted {len(messages)} messages')
