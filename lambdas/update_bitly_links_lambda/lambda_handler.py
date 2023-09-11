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
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    os.chdir('/tmp')
    COMPANY = os.environ[constants.ENV_PARTNER]
    BITLY_KEY = os.environ[constants.ENV_PARTNER_SMS_KEY]
    BUCKET_NAME = os.environ[constants.ENV_BUCKET_NAME]
    S3_KEY = os.environ[constants.S3_KEY]
    s3_path = f'{S3_KEY}/{COMPANY}_sms_totals.csv'
    s3 = boto3.client('s3')
    s3.download_file(BUCKET_NAME, s3_path, f'{COMPANY}_sms_totals.csv')

    response = aws_handler.get_secret(BITLY_KEY)
    BITLY_KEY = response[0]['password']
    try:
        logger.info('making API call to bitly for everything but clicks')
        bitly = bitly_handler.BitlyData(bitly_key=BITLY_KEY, company=COMPANY)
        df = bitly.make_api_call()
        df.to_csv('test.csv', index=False)
        s3.upload_file('test.csv', BUCKET_NAME, f'{S3_KEY}/test.csv')
    except Exception as e:
        logger.error(f'Encountered error with API Call: {e}')
    try:
        logger.info('compiling data into totals pd object')
        combineddf = bitly.shape_df(df)
    except:
        logger.error('error made concantenating data')
    try:
        logger.info('making api calls to get total clicks')
        with_clicks = bitly.get_click_totals(combineddf)
    except:
        logger.error('had issue getting clicks, check if exceeded api limit')
    ts = pd.to_datetime('now')
    file_name = f'{COMPANY}_sms_totals_{ts.year}_{ts.month}_{ts.day}.csv'
    with_clicks = with_clicks.reset_index(drop=True)
    with_clicks.to_csv(f'{COMPANY}_sms_totals.csv', index=False)
    s3.upload_file('clicks_needed.csv', BUCKET_NAME, f'{S3_KEY}/clicks_needed.csv')
    s3.upload_file(f'{COMPANY}_sms_totals.csv', BUCKET_NAME, s3_path)
    archive_s3_path = f'{S3_KEY}/archive/{file_name}'
    s3.upload_file(f'{COMPANY}_sms_totals.csv', BUCKET_NAME, archive_s3_path)
    ts = pd.to_datetime('now')
    logger.info(f'hour of lambda execution: {ts.hour}')
