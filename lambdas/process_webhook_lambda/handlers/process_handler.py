import os
import json
from utils import *
from constants import *
from handlers.s3_handler import S3Handler
from handlers.sqs_handler import SQSHandler


def sqs_to_s3_handler() -> None:
    """
    Process handler for sqs to s3. Picks messages from sqs and uploads them to s3 in CSV
    """
    queue_name = os.environ.get(ENV_WEBHOOKS_QUEUE_NAME)
    bucket_name = os.environ.get(ENV_S3_BUCKET_NAME)
    max_batch_size = int(os.environ.get(ENV_QUEUE_MAX_BATCH_SIZE))
    max_wait_time = int(os.environ.get(ENV_QUEUE_MAX_WAIT_TIME))
    messages_polling_limit = int(os.environ.get(ENV_MESSAGES_POLLING_LIMIT)) or MESSAGES_POLLING_LIMIT_DEFAULT

    # Receives messages from sqs in bulk
    sqs_handler = SQSHandler(
        queue_name=queue_name,
        max_batch_size=max_batch_size,
        max_wait_time=max_wait_time,
        messages_polling_limit=messages_polling_limit
    )
    sqs_messages = sqs_handler.receive_messages()

    # Split those messages by record type i.e. bounce, spam etc.
    messages = list(map(lambda msg: json.loads(msg.body), sqs_messages))
    record_type_dict = split_list_based_on_key(messages, 'RecordType', 'inbound')

    # For each record type, convert messages to csv and upload to S3
    for key, value in record_type_dict.items():
        csv_string = convert_json_to_csv(value)
        S3Handler(bucket_name=bucket_name).upload_csv(record_type=key, data=csv_string)

    # After uploading, delete messages from queue
    sqs_handler.delete_messages(messages=sqs_messages)
