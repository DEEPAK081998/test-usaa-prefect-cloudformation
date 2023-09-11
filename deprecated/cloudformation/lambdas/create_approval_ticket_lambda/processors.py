import json


def get_codepipeline_info(data: dict) -> dict:
    """
    Get codepipeline info from event data dict
    :param event: event data dict
    :return: codepipeline info dict
    """
    token = data["approval"]["token"]
    codepipeline_name = data["approval"]["pipelineName"]
    custom_data = data["approval"]["customData"]

    return {
        'token': token,
        'codepipeline_name': codepipeline_name,
        'custom_data': custom_data
    }


def generate_create_issue_request_body(info: dict) -> dict:
    """
    Generate create issue request body from codepipeline info
    :param info: info dict
    :return: create issue request body dict
    """
    payload = json.dumps({
        "fields": {
            "summary": '{codepipeline_name}___manual_approval___{env}___{token}'.format_map(info),
            "issuetype": {
                "name": info['issue_type']
            },
            "project": {
                "key": info['project_key']
            },
            "assignee": {
                "id": info['assignee_id']
            },
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": info['custom_data']
                            }
                        ]
                    }
                ]
            },
        },
    })

    return payload
