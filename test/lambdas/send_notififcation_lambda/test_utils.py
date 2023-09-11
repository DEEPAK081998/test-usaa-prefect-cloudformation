import json
import unittest
from unittest import mock

from lambdas.send_notification_lambda import utils


class TestUtils(unittest.TestCase):
    """
    Class to test all functions in utils.py
    """

    @mock.patch('urllib3.PoolManager')
    def test_send_message_valid(self, mock_pool_manager: unittest.mock.MagicMock) -> None:
        """
        Test for send message function with valid data
        :param mock_pool_manager: urllib mock pool manager
        """
        message = {'hello': 'world'}
        utils.send_message(url='http://localhost.com', message=message)
        mock_pool_manager.return_value.request.assert_called_once_with(
            'POST',
            'http://localhost.com',
            body=json.dumps(message).encode('utf-8')
        )

    @mock.patch('urllib3.PoolManager')
    def test_send_message_none(self, mock_pool_manager: unittest.mock.MagicMock) -> None:
        """
        Test for send message function with empty data
        :param mock_pool_manager: urllib mock pool manager
        """
        message = {}
        utils.send_message(url='http://localhost.com', message=message)
        mock_pool_manager.return_value.request.assert_not_called()

    def test_get_pipline_info_for_started_event(self) -> None:
        """
        Test get_pipeline_info function for started event data
        """
        input_data = {
            'account': '1234',
            'detailType': 'CodePipeline Pipeline Execution State Change',
            'region': 'us-east-1',
            'source': 'aws.codepipeline',
            'time': '2022-08-23T11:07:17Z',
            'notificationRuleArn': 'arn:aws:codestar-notifications:us-east-1:1234:notificationrule/1234',
            'detail': {
                'pipeline': 'test-pipeline',
                'execution-id': 'b7c9a84b-aebf-4f02-9a6a-336282893747',
                'execution-trigger': {
                    'trigger-type': 'StartPipelineExecution',
                    'trigger-detail': 'arn:aws:sts::1234:assumed-role/sample_role/sample_user'
                },
                'state': 'STARTED',
                'version': 1.0
            },
            'resources': ['arn:aws:codepipeline:us-east-1:1234:test-pipeline'],
            'additionalAttributes': {}
        }
        expected_data = {
            'status': 'STARTED',
            'name': 'test-pipeline',
            'link': (
                'https://console.aws.amazon.com/codesuite/codepipeline/pipelines/test-pipeline/view?region=us-east-1'
            )
        }
        actual_data = utils.get_pipline_info(data=input_data)
        self.assertDictEqual(actual_data, expected_data)

    def test_get_pipline_info_for_approval_event(self) -> None:
        """
        Test get_pipeline_info function for approval event data
        """
        input_data = {
            'region': 'us-east-1',
            'consoleLink': (
                'https://console.aws.amazon.com/codesuite/codepipeline/pipelines/test-pipeline/view?region=us-east-1'
            ),
            'approval': {
                'pipelineName': 'test-pipeline',
                'stageName': 'Approval',
                'actionName': 'ManualApproval',
                'token': '0c35520a-b7e6-403d-ba3f-e02120b524c3',
                'expires': '2022-08-30T11:09Z',
                'externalEntityLink': None,
                'approvalReviewLink': (
                    'https://console.aws.amazon.com/codesuite/codepipeline/pipelines/test-pipeline/'
                    'view?region=us-east-1#/Approval/ManualApproval/approve/0c35520a-b7e6-403d-ba3f-e02120b524c3'
                ),
                'customData': (
                    'Testing of all dags, flows and connection is completed, '
                    'please approve to deploy flows and connection\\n'
                )
            }
        }
        expected_data = {
            'status': 'Approval Needed',
            'name': 'test-pipeline',
            'link': (
                'https://console.aws.amazon.com/codesuite/codepipeline/pipelines/test-pipeline/view?region=us-east-1'
            ),
            'approval_message': (
                'Testing of all dags, flows and connection is completed, '
                'please approve to deploy flows and connection\\n'
            ),
            'approval_link': (
                'https://console.aws.amazon.com/codesuite/codepipeline/pipelines/test-pipeline/'
                'view?region=us-east-1#/Approval/ManualApproval/approve/0c35520a-b7e6-403d-ba3f-e02120b524c3'
            )
        }
        actual_data = utils.get_pipline_info(data=input_data)
        self.assertDictEqual(actual_data, expected_data)

    def test_get_pipline_info_for_failed_event(self) -> None:
        """
        Test get_pipeline_info function for failed event data
        """
        input_data = {
            "account": "1234",
            "detailType": "CodePipeline Pipeline Execution State Change",
            "region": "us-east-1",
            "source": "aws.codepipeline",
            "time": "2022-08-24T10:16:14Z",
            "notificationRuleArn": "arn:aws:codestar-notifications:us-east-1:1234:notificationrule/1234",
            "detail": {
                "pipeline": "test-pipeline",
                "execution-id": "0a16e1e1-cd3f-4e81-b2e6-bbd9d78b2967",
                "state": "FAILED",
                "version": 1.0
            },
            "resources": [
                "arn:aws:codepipeline:us-east-1:1234:test-pipeline"],
            "additionalAttributes": {
                "failedActionCount": 2,
                "failedActions": [{
                    "action": "TestAirbyteConnections",
                    "additionalInformation": "Build terminated with state: FAILED"
                }, {
                    "action": "TestAirbyteConnections",
                    "additionalInformation": "Build terminated with state: FAILED"
                }],
                "failedStage": "TEST"
            }
        }
        expected_data = {
            'status': 'FAILED',
            'name': 'test-pipeline',
            'link': (
                'https://console.aws.amazon.com/codesuite/codepipeline/pipelines/test-pipeline/view?region=us-east-1'
            ),
            'failed_stage': 'TEST',
            'failed_info': [
                {'action': 'TestAirbyteConnections', 'additionalInformation': 'Build terminated with state: FAILED'},
                {'action': 'TestAirbyteConnections', 'additionalInformation': 'Build terminated with state: FAILED'}]
        }
        actual_data = utils.get_pipline_info(data=input_data)
        self.assertDictEqual(actual_data, expected_data)

    def test_get_pipline_info_for_random_event(self) -> None:
        """
        Test get_pipeline_info function for random event data
        """
        input_data = {
            "account": "1234",
            "detailType": "sample message",
            "region": "us-east-1",
            "source": "aws.sns",
            "time": "2022-08-24T10:16:14Z",
            "notificationRuleArn": "arn:aws:codestar-notifications:us-east-1:1234:notificationrule/1234",
            "message": "hello world"
        }
        expected_data = {}
        actual_data = utils.get_pipline_info(data=input_data)
        self.assertDictEqual(actual_data, expected_data)
