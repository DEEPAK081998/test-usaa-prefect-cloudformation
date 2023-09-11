import os
import logging
from clients.jira_client import JiraAPIClass
import connectors
import processors

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MANUAL_APPROVAL_PROJECT_KEY = os.environ['MANUAL_APPROVAL_PROJECT_KEY']
MANUAL_APPROVAL_PROJECT_ROLE = os.environ['MANUAL_APPROVAL_PROJECT_ROLE']
JIRA_DOMAIN_NAME = os.environ['JIRA_DOMAIN_NAME']
JIRA_SECRETS_ARN = os.environ['JIRA_SECRETS_ARN']

def lambda_handler(event, context):
    logger.info(f'Event info {event}')
    try:
        action_details = processors.get_action_details(event=event)

        if 'approve' not in action_details:
            logger.info('Did not recieve approval or rejection comment')
            return processors.format_response(200, 'Did not recieve approval or rejection comment')

        if MANUAL_APPROVAL_PROJECT_ROLE:
            base_path = JiraAPIClass.get_base_path_from_jira_domain(JIRA_DOMAIN_NAME)
            jira_secrets = connectors.fetch_secrets(secret_arn=JIRA_SECRETS_ARN)
            jira_api_client = JiraAPIClass(base_url=base_path, username=jira_secrets['username'], password=jira_secrets['token'])
            project_role = jira_api_client.get_project_role(project=MANUAL_APPROVAL_PROJECT_KEY, role=MANUAL_APPROVAL_PROJECT_ROLE)
            processors.validate_user_in_project_role(role_details=project_role, user_id=action_details['commentor_id'])

        approval_response = connectors.update_codepipeline_status(action_details=action_details)
        logger.info(f'Codepipeline status updated successfully: {approval_response}')
        return processors.format_response(200, 'Codepipeline status updated successfully')

    except Exception as e:
        logger.error(f'Error while updating codepipeline status: {e}')
        return processors.format_response(500, 'Codepipeline status updation failed')
