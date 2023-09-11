import json


def get_action_details(event: dict) -> dict:
    """
    Get update codepipeline action details dict
    :param event: Lambda event object
    :return: action details dict
    """
    pipeline_info = event["issue"]["fields"]["summary"].split("___")
    if len(pipeline_info) < 4:
        raise Exception(f'Insufficient codepipeline info: {pipeline_info}')
    codepipeline_name = pipeline_info[0]
    token = pipeline_info[3]
    comment = event["comment"]["body"]
    user_id = event["comment"]["author"]["accountId"]
    action_details = {
        "codepipeline_token": token,
        "codepipeline_name": codepipeline_name,
        "commentor_id": user_id
    }
    if (comment == "Approved" or comment == "approved"):
        action_details['approve'] = True
    elif (comment == "Rejected" or comment == "rejected"):
        action_details['approve'] = False
    return action_details


def format_response(status_code, message: str) -> dict:
    """
    Format response for API gateway based on status code and message
    :param status_code: response status code
    :param message: response message
    :return: format response dict
    """
    body = {'message': message}
    formatted_body = json.dumps(body)
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "isBase64Encoded": False,
        "body": formatted_body
    }


def validate_user_in_project_role(role_details: dict, user_id: str):
    """
    Validate user in project role
    :param role_details: role details dict
    :param user_id: user id
    """
    user_validated = False
    actors = role_details['actors']
    for actor in actors:
        if 'actorUser' in actor and actor['actorUser']['accountId'] == user_id:
            user_validated = True
    if not user_validated:
        name = role_details['name']
        raise Exception(f'User with id {user_id} does not exist in role {name}')
