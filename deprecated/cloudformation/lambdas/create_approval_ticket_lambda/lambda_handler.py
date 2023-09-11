import os
import json
import logging
import processors
import connectors
from clients.jira_client import JiraAPIClass

JIRA_DOMAIN_NAME = os.environ['JIRA_DOMAIN_NAME']
JIRA_SECRETS_ARN = os.environ['JIRA_SECRETS_ARN']
MANUAL_APPROVAL_PROJECT_KEY = os.environ['MANUAL_APPROVAL_PROJECT_KEY']
MANUAL_APPROVAL_ISSUE_TYPE = os.environ['MANUAL_APPROVAL_ISSUE_TYPE']
MANUAL_APPROVAL_ASSIGNEE_ID = os.environ['MANUAL_APPROVAL_ASSIGNEE_ID']
ENVIRONMENT = os.environ['ENVIRONMENT']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    # Take out message from SNS Topic
    logger.info(f'Event info {event}')
    try:
        message = event["Records"][0]["Sns"]["Message"]
        data = json.loads(message)

        if "approval" in data:
            # if key 'approval' is not present in data then it means that the incoming event is not a
            # manual approval event, hence no need to create jira ticket
            info = processors.get_codepipeline_info(data=data)
            info['env'] = ENVIRONMENT
            info['project_key'] = MANUAL_APPROVAL_PROJECT_KEY
            info['issue_type'] = MANUAL_APPROVAL_ISSUE_TYPE
            info['assignee_id'] = MANUAL_APPROVAL_ASSIGNEE_ID
            body = processors.generate_create_issue_request_body(info=info)
            base_path = JiraAPIClass.get_base_path_from_jira_domain(JIRA_DOMAIN_NAME)
            jira_secrets = connectors.fetch_secrets(secret_arn=JIRA_SECRETS_ARN)
            jira_api_client = JiraAPIClass(base_url=base_path, username=jira_secrets['username'], password=jira_secrets['token'])
            body = jira_api_client.create_issue(body=body)
            logger.info(f'Successfully created approval ticket with data: {body}')
        else:
            state = data['detail']['state']
            logger.info(f'Pipeline event recieved with state: {state}')
    except Exception as e:
        logger.exception(f'Error while lambda execution {e}')
