import json

import urllib3


def get_pipline_info(data: dict) -> dict:
    """
    Extract information of pipline form given message
    :param data: data dict to extract info from
    :return: extracted info dict
    """
    config = {}
    # checks if the message is for approval notification
    if 'approval' in data:
        config = {
            'status': 'Approval Needed',
            'name': data['approval']['pipelineName'],
            'link': data['consoleLink'],
            'approval_message': data['approval']['customData'],
            'approval_link': data['approval']['approvalReviewLink']
        }

    # checks if the message is for pipline status change
    elif 'codepipeline' in data.get('source') and 'Action' not in data.get('detailType'):
        config = {
            'status': data['detail']['state'],
            'name': data['detail']['pipeline'],
            'link': (
                f"https://console.aws.amazon.com/codesuite/codepipeline/pipelines/"
                f"{data['detail']['pipeline']}/view?region={data['region']}"
            )
        }
        if data.get('additionalAttributes') and 'failedStage' in data.get('additionalAttributes'):
            config['failed_stage'] = data['additionalAttributes']['failedStage']
            config['failed_info'] = data['additionalAttributes'].get('failedActions', [])
    return config


def send_message(url: str, message: dict) -> urllib3.response.HTTPResponse:
    """
    Send encoded message to the given url
    :param url: url where to send message
    :param message: message data to send
    :return: request response
    """
    http = urllib3.PoolManager()
    if message:
        encoded_msg = json.dumps(message).encode("utf-8")
        response = http.request("POST", url, body=encoded_msg)
        return response
