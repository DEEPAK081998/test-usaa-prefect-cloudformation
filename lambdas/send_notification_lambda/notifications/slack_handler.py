import logging

import utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('slack_notification_handler')
logger.setLevel(level=logging.INFO)


def _generate_slack_message_for_pipeline(slack_channel: str, config: dict) -> dict:
    """
    Generates pipeline message template for slack
    :param slack_channel: slack channel
    :param config: config dict
    :return: message template dict
    """
    msg = {
        "channel": slack_channel,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Pipeline Update"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Pipeline:*\n<{config['link']}|{config['name']}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{config['status']}"
                    }
                ]
            }
        ]
    }
    if 'approval_message' in config and 'approval_link' in config:
        msg['blocks'].extend(
            [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Custom message:*\n{config['approval_message']}"
                    }

                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<{config['approval_link']}|View approval request>"
                    }
                }
            ]
        )
    elif 'failed_stage' in config:
        msg['blocks'].append({"type": "divider"})
        for failed_action in config['failed_info']:
            msg['blocks'].append(
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Action:*\n{failed_action['action']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Additional Info:*\n{failed_action['additionalInformation']}"
                        }
                    ]
                }
            )
        msg['blocks'].append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Stage:* {config['failed_stage']}"
                }
            }
        )
    return msg


def send_slack_notification(slack_url: str, slack_channel: str, pipeline_info: dict = None) -> None:
    """
    Send slacks notification
    :param slack_url: slack webhook url
    :param slack_channel: slack channel
    :param pipeline_info: pipeline config message to send
    """

    if pipeline_info:
        message = _generate_slack_message_for_pipeline(slack_channel=slack_channel, config=pipeline_info)
        resp = utils.send_message(url=slack_url, message=message)
        logger.info(f'Pipeline message sent got response [status_code: {resp.status}, response: {resp.data}]')
