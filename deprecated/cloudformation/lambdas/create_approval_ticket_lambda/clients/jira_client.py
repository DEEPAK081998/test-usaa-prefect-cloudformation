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

    @staticmethod
    def get_base_path_from_jira_domain(domain: str) -> str:
        """
        Get Jira Rest API base path from jira domain name
        :param domain: domain name
        :return: Jira rest API base url
        """
        return f'https://{domain}/rest/api/3/'

    def _create(self, body: dict, path: str) -> dict:
        """
        Makes a Create request
        :param body: request body
        :param path: api path
        :return: response dict
        """
        logger.debug(f'body={body} path={path}')
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
