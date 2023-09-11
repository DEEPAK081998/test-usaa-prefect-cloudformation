import logging
from http import HTTPStatus
from clients.base_client import BaseAPIClass
import constants

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class JiraAPIClass(BaseAPIClass):

    def __init__(self, base_url: str, username: str, password: str) -> None:
        """
        Initialize the Jira API class
        :param base_url: API base url
        """
        super().__init__()
        self.BASE_URL = base_url
        self.USERNAME = username
        self.PASSWORD = password

    @staticmethod
    def _check_for_error(status_code: int, data: dict or str) -> None:
        """
        Check if the response have any error or not
        :param status_code: Response status code
        :param data: response data
        """
        if status_code == HTTPStatus.BAD_REQUEST:
            raise ValueError(
                f'Validation failed got response {status_code}, error {data}')
        elif status_code == HTTPStatus.UNAUTHORIZED:
            raise Exception(
                f'Unauthorized request got response {status_code}, error {data}')
        elif status_code == HTTPStatus.FORBIDDEN:
            raise Exception(
                f'Forbidden request got response {status_code}, error: {data}')
        elif status_code == HTTPStatus.CONFLICT:
            raise Exception(
                f'Got response {status_code}, error: {data}')

    @staticmethod
    def get_base_path_from_jira_domain(domain: str) -> str:
        """
        Get Jira Rest API base path from jira domain name
        :param domain: domain name
        :return: Jira rest API base url
        """
        return f'https://{domain}/rest/api/3/'

    def _get(self, path: str, param: dict = None) -> dict:
        """
        Makes a Get request
        :param body: request body
        :param path: api path
        :return: response dict
        """
        logging.debug(f'GET request path={path}')
        status_code, data = self.get(path=path)
        self._check_for_error(status_code=status_code, data=data)
        return data

    def _create(self, body: dict, path: str) -> dict:
        """
        Makes a Create request
        :param body: request body
        :param path: api path
        :return: response dict
        """
        logger.debug(f'POST request: body={body} path={path}')
        status_code, data = self.post(path=path, data=body)
        self._check_for_error(status_code=status_code, data=data)
        return data

    def create_issue(self, body: dict) -> dict:
        """
        Create an issue on JIRA
        :param body: request body
        :return: response dict
        """
        return self._create(body=body, path=constants.ISSUE)

    def get_project_role(self, project: str, role: str) -> dict:
        """
        Get project role details
        :param project: project key
        :param role: role name
        :return: response dict
        """
        path = f'{constants.PROJECT}/{project}/{constants.ROLE}/'
        data = self._get(path=path)  # get all roles for the project
        if role in data:
            role_url: str = data[role]
            role_id = role_url.split('/')[-1]
            role_path = f'{path}/{role_id}'
            return self._get(path=role_path)  # get intended project role
        else:
            raise Exception(
                f'Project role {role} does not exist in project {project}')

    def get_user(self, email: str) -> dict:
        """
        Get user details
        :param email: user email address
        :return: response dict
        """
        path = f'{constants.USER}/{constants.SEARCH}'
        param = {'query': email}
        data = self._get(path=path, param=param)
        if len(data) == 0:
            raise Exception(f'User with email: {email} not found')
        else:
            return data
