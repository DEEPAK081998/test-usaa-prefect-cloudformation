from handlers import process_handler


def lambda_handler(event, context):
    """
    Main Driver function
    """
    # process webhook data present in sqs and upload it to s3
    process_handler.sqs_to_s3_handler()
