import json
import os

import constants
import utils
from notifications import slack_handler


def send_notification(event: dict) -> None:
    """
    Sends notification to the desired apps/webhooks
    :param event: event dict
    """
    slack_url = os.environ[constants.ENV_SLACK_WEBHOOK_URL]
    slack_channel = os.environ[constants.ENV_SLACK_CHANNEL]
    data = json.loads(event["Records"][0]["Sns"]["Message"])
    pipeline_info = utils.get_pipline_info(data)
    slack_handler.send_slack_notification(slack_url=slack_url, slack_channel=slack_channel, pipeline_info=pipeline_info)
