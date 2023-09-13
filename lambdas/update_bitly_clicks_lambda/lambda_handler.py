import boto3
import logging
import pandas as pd
import os
from typing import Any, Dict

import constants
from handlers import aws_handler, bitly_handler


def lambda_handler(event: Dict[str, Any], context: Dict[str, Any]) -> None:
    """
    Main driver function
    """
    print("hello world")
    # logger = logging.getLogger()
    # logger.setLevel(logging.INFO)
    # COMPANY = os.environ[constants.ENV_PARTNER]
    # BUCKET_NAME = os.environ[constants.ENV_BUCKET_NAME]
    # S3_KEY = os.environ[constants.S3_KEY]
    # s3 = boto3.client('s3')
    # os.chdir('/tmp')
    # s3.download_file(BUCKET_NAME, f'{S3_KEY}/clicks_needed.csv', 'clicks_needed.csv')

    # ts = pd.to_datetime('now')
    # logger.info(f'hour executed {ts.hour}')
    # file_stats = os.stat('clicks_needed.csv')
    # # check to see if any api calls are needed, if so run this code
    # # if not terminate the lambda
    # if file_stats.st_size > 1 and ts.hour != 8:
    #     outstanding_bitly = pd.read_csv('clicks_needed.csv')
    #     BITLY_KEY = os.environ[constants.ENV_PARTNER_SMS_KEY]
    #     response = aws_handler.get_secret(BITLY_KEY)
    #     BITLY_SECRET = response[0]['password']
    #     s3_path = f'{S3_KEY}/{COMPANY}_sms_totals.csv'
    #     s3.download_file(BUCKET_NAME, s3_path, f'{COMPANY}_sms_totals.csv')
    #     bitly_totals = pd.read_csv(f'{COMPANY}_sms_totals.csv')
    #     new_total = bitly_handler.get_click_counts(bitly_totals, outstanding_bitly, BITLY_SECRET)
    #     new_total.to_csv(f'{COMPANY}_sms_totals.csv', index=False)
    #     s3.upload_file('clicks_needed_updated.csv', BUCKET_NAME, f'{S3_KEY}/clicks_needed.csv')
    #     s3.upload_file(f'{COMPANY}_sms_totals.csv', BUCKET_NAME, s3_path)
    #     if ts.hour == 5:
    #         logger.warning('click counter is at 50% capacity')
    #     if ts.hour == 8:
    #         logger.error('out of capacity')
    # else:
    #     logger.info('no bitly links needed')
