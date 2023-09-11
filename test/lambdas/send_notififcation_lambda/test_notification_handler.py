import json
import os
import unittest
from unittest import mock

from lambdas.send_notification_lambda import constants
from lambdas.send_notification_lambda.notifications import notification_handler


class TestNotificationHandler(unittest.TestCase):
    """
    Class to test notification handler
    """

    def setUp(self) -> None:
        """
        Test setup
        :return:
        """
        self.slack_url = 'http://localhost.com/webhook/test123'
        self.slack_channel = 'test-channel'

    @mock.patch('urllib3.PoolManager')
    def _send_and_check_notification(
        self, mock_pool_manager: unittest.mock.MagicMock, event: dict, expected_data: dict
    ) -> None:
        """
        Call notification handler send_notification function and check for expected message
        :param mock_pool_manager: urllib pool manager
        :param event: event to send notification for
        :param expected_data: expected data to get from sent notification
        """
        os.environ[constants.ENV_SLACK_WEBHOOK_URL] = self.slack_url
        os.environ[constants.ENV_SLACK_CHANNEL] = self.slack_channel
        notification_handler.send_notification(event=event)
        if expected_data:
            mock_pool_manager.return_value.request.assert_called_once_with(
                'POST',
                self.slack_url,
                body=json.dumps(expected_data).encode('utf-8')
            )
        else:
            mock_pool_manager.return_value.request.assert_not_called()
        del os.environ[constants.ENV_SLACK_WEBHOOK_URL]
        del os.environ[constants.ENV_SLACK_CHANNEL]

    def test_notification_handler_for_started_event(self) -> None:
        """
        Test notification handler for pipeline started event
        """
        event = {
            "Records": [{
                "EventSource": "aws:sns",
                "EventVersion": "1.0",
                "EventSubscriptionArn": "arn:aws:sns:us-east-1:429533234373:airflow-infra-sandbox-manual-approval-topic:abf270ea-576b-4f86-b662-8627af8e16ed",
                "Sns": {
                    "Type": "Notification",
                    "MessageId": "68758ad2-bc45-5a98-a69c-d1ac0b68e350",
                    "TopicArn": "arn:aws:sns:us-east-1:429533234373:airflow-infra-sandbox-manual-approval-topic",
                    "Subject": None,
                    "Message": "{\"account\":\"429533234373\",\"detailType\":\"CodePipeline Pipeline Execution State Change\",\"region\":\"us-east-1\",\"source\":\"aws.codepipeline\",\"time\":\"2022-08-23T11:07:17Z\",\"notificationRuleArn\":\"arn:aws:codestar-notifications:us-east-1:429533234373:notificationrule/1571a76057cb58da0ce02ba84d38d93afa5a72b6\",\"detail\":{\"pipeline\":\"vrathore-slack-test2-sandbox-pipeline\",\"execution-id\":\"b7c9a84b-aebf-4f02-9a6a-336282893747\",\"execution-trigger\":{\"trigger-type\":\"StartPipelineExecution\",\"trigger-detail\":\"arn:aws:sts::429533234373:assumed-role/RE-Sandbox_only_dev_JTG/vrathore@homestoryrewards.com\"},\"state\":\"STARTED\",\"version\":1.0},\"resources\":[\"arn:aws:codepipeline:us-east-1:429533234373:vrathore-slack-test2-sandbox-pipeline\"],\"additionalAttributes\":{}}",
                    "Timestamp": "2022-08-23T11:07:25.806Z",
                    "SignatureVersion": "1",
                    "Signature": "KLx9KVlrvZv3O5g/X5nPfogccKzhCTan7yXxFd55XCajR118QImA9SGpZIMqteWB4pCixgtE3xRLZ+2TfR6ZO2ECZJDW8k2jI9ui+n+gy4cE7NhfXgV8HVHPwwgzP8GE7w4q41JpJ6RyuPKlyNjyCvtuG/Q3FDYzDsTM+1sacavar8HXCN1Iyc4UDSE+YLG+6bdlHUHy/QfxAbmeDdd5LptG7erB/LaW5qiIGPgmrSljvtma6Ufbs0F/CPKme0unWsV7/QZD5AUXsjWhcQRqs1gWvxybOYrgHyI6TgNYjLNfFeRKdIZU5mV/YQ2c/mA0oDdSfaL/rcMh86gGWfD1+Q==",
                    "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-56e67fcb41f6fec09b0196692625d385.pem",
                    "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:429533234373:airflow-infra-sandbox-manual-approval-topic:abf270ea-576b-4f86-b662-8627af8e16ed",
                    "MessageAttributes": {}
                }
            }]
        }
        expected_data = {
            "channel": "test-channel",
            "blocks": [{"type": "header", "text": {"type": "plain_text", "text": "Pipeline Update"}}, {
                "type": "section",
                "fields": [{
                    "type": "mrkdwn",
                    "text": "*Pipeline:*\n<https://console.aws.amazon.com/codesuite/codepipeline/pipelines/vrathore-slack-test2-sandbox-pipeline/view?region=us-east-1|vrathore-slack-test2-sandbox-pipeline>"
                }, {"type": "mrkdwn", "text": "*Status:*\nSTARTED"}]
            }]
        }
        self._send_and_check_notification(event=event, expected_data=expected_data)

    def test_notification_handler_for_approval_event(self) -> None:
        """
        Test notification handler for pipeline approval event
        """
        event = {
            "Records": [{
                "EventSource": "aws:sns",
                "EventVersion": "1.0",
                "EventSubscriptionArn": "arn:aws:sns:us-east-1:429533234373:airflow-infra-sandbox-manual-approval-topic:abf270ea-576b-4f86-b662-8627af8e16ed",
                "Sns": {
                    "Type": "Notification",
                    "MessageId": "341a58fe-f662-55aa-b071-038041d6eb47",
                    "TopicArn": "arn:aws:sns:us-east-1:429533234373:airflow-infra-sandbox-manual-approval-topic",
                    "Subject": "APPROVAL NEEDED: AWS CodePipeline vrathore-slack-test2-san... for action ManualApproval",
                    "Message": "{\"region\":\"us-east-1\",\"consoleLink\":\"https://console.aws.amazon.com/codesuite/codepipeline/pipelines/vrathore-slack-test2-sandbox-pipeline/view?region=us-east-1\",\"approval\":{\"pipelineName\":\"vrathore-slack-test2-sandbox-pipeline\",\"stageName\":\"Approval\",\"actionName\":\"ManualApproval\",\"token\":\"0c35520a-b7e6-403d-ba3f-e02120b524c3\",\"expires\":\"2022-08-30T11:09Z\",\"externalEntityLink\":null,\"approvalReviewLink\":\"https://console.aws.amazon.com/codesuite/codepipeline/pipelines/vrathore-slack-test2-sandbox-pipeline/view?region=us-east-1#/Approval/ManualApproval/approve/0c35520a-b7e6-403d-ba3f-e02120b524c3\",\"customData\":\"Testing of all dags, flows and connection is completed, please approve to deploy flows and connection\\n\"}}",
                    "Timestamp": "2022-08-23T11:09:40.068Z",
                    "SignatureVersion": "1",
                    "Signature": "lrSmXRSJpGMvirA0dGSRRIVH8MmTuSlsWyyK218hab9FMSwoZnCx7q1Hnj/b945+dK3/9N/sSI6lsyI92AKhGSd1XtEQZj7KQBvcZt4NpT/5pLykg4DBbsPMmATiwFQrcpEtiivSahqfq7YW8r6oj3ZZ/vG80D8HynapqoIxCLGiqEXKA+5kAwceVo8lx1y9XYQnVvACHBX9z+ohGj7aT9Me53aZOhnrX9V5rmTTl96Xj6HqDUDkh79SVeHadFyFRYrKX+3c+M1DVZGjNPXVi8zvXT2wn6alHsxVY3CrdHVbwfAKObosF+Idasb1SKY0P3/k2nNUnb4Hi3IPhir/pg==",
                    "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-56e67fcb41f6fec09b0196692625d385.pem",
                    "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:429533234373:airflow-infra-sandbox-manual-approval-topic:abf270ea-576b-4f86-b662-8627af8e16ed",
                    "MessageAttributes": {}
                }
            }]
        }
        expected_data = {
            "channel": "test-channel",
            "blocks": [{"type": "header", "text": {"type": "plain_text", "text": "Pipeline Update"}}, {
                "type": "section",
                "fields": [{
                    "type": "mrkdwn",
                    "text": "*Pipeline:*\n<https://console.aws.amazon.com/codesuite/codepipeline/pipelines/vrathore-slack-test2-sandbox-pipeline/view?region=us-east-1|vrathore-slack-test2-sandbox-pipeline>"
                }, {"type": "mrkdwn", "text": "*Status:*\nApproval Needed"}]
            }, {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Custom message:*\nTesting of all dags, flows and connection is completed, please approve to deploy flows and connection\n"
                }
            }, {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "<https://console.aws.amazon.com/codesuite/codepipeline/pipelines/vrathore-slack-test2-sandbox-pipeline/view?region=us-east-1#/Approval/ManualApproval/approve/0c35520a-b7e6-403d-ba3f-e02120b524c3|View approval request>"
                }
            }]
        }
        self._send_and_check_notification(event=event, expected_data=expected_data)

    def test_notification_handler_for_failed_event(self) -> None:
        """
        Test notification handler for pipeline failed event
        """
        event = {
            "Records": [
                {
                    "EventSource": "aws:sns",
                    "EventVersion": "1.0",
                    "EventSubscriptionArn": "arn:aws:sns:us-east-1:429533234373:airflow-infra-sandbox-manual-approval-topic:abf270ea-576b-4f86-b662-8627af8e16ed",
                    "Sns": {
                        "Type": "Notification",
                        "MessageId": "302ff896-60ff-5926-b7d4-a3e99c46ba0c",
                        "TopicArn": "arn:aws:sns:us-east-1:429533234373:airflow-infra-sandbox-manual-approval-topic",
                        "Subject": None,
                        "Message": '{"account": "429533234373", "detailType": "CodePipeline Pipeline Execution State Change", "region": "us-east-1", "source": "aws.codepipeline", "time": "2022-08-24T10:16:14Z", "notificationRuleArn": "arn:aws:codestar-notifications:us-east-1:429533234373:notificationrule/f2eef3cee4fb590b6d92d7fa733d413cdad058e7", "detail": {"pipeline": "workflow-resources-pipeline-test-sandbox-pipeline", "execution-id": "0a16e1e1-cd3f-4e81-b2e6-bbd9d78b2967", "state": "FAILED", "version": 1.0}, "resources": ["arn:aws:codepipeline:us-east-1:429533234373:workflow-resources-pipeline-test-sandbox-pipeline"], "additionalAttributes": {"failedActionCount": 2, "failedActions": [{"action": "TestAirbyteConnections", "additionalInformation": "Build terminated with state: FAILED"}, {"action": "TestAirbyteConnections", "additionalInformation": "Build terminated with state: FAILED"}], "failedStage": "TEST"}}',
                        "Timestamp": "2022-08-24T10:16:25.676Z",
                        "SignatureVersion": "1",
                        "Signature": "q05Zr1u05BuF2k5v3qIMR3wo9fptzeYU9jAw17rvx539A/RNdEOkT5u28x9NpkenCc0YFZtcmWUL1mLOA7gdE1IrYJZXU4bz/pNKXS/akz9leXCCe2VLRaOcmmpbSRBBBbbjQNlA5mBovpyoRgOX1cDCLjKt8LrldcqshOlZKCPzz8JRmhpnopJ3PyHjYTUS5QjBRrmBIjz81GaS8hbUebczV4oUE3AyhyqVCuvMMijdr1RHDv6O09+kJvjzBckYsvkyrDZ2WOgG4jaPPp7lCWXZoEzVdozB3yKDYJ+RG22zemqfzSNvdpoF8hYyJmuHQXc/oW0uDDy5B5ECukOo7g==",
                        "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-56e67fcb41f6fec09b0196692625d385.pem",
                        "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:429533234373:airflow-infra-sandbox-manual-approval-topic:abf270ea-576b-4f86-b662-8627af8e16ed",
                        "MessageAttributes": {}
                    }
                }
            ]
        }
        expected_data = {
            "channel": "test-channel",
            "blocks": [{"type": "header", "text": {"type": "plain_text", "text": "Pipeline Update"}}, {
                "type": "section",
                "fields": [{
                    "type": "mrkdwn",
                    "text": "*Pipeline:*\n<https://console.aws.amazon.com/codesuite/codepipeline/pipelines/workflow-resources-pipeline-test-sandbox-pipeline/view?region=us-east-1|workflow-resources-pipeline-test-sandbox-pipeline>"
                }, {"type": "mrkdwn", "text": "*Status:*\nFAILED"}]
            }, {"type": "divider"}, {
                "type": "section",
                "fields": [{"type": "mrkdwn", "text": "*Action:*\nTestAirbyteConnections"},
                    {"type": "mrkdwn", "text": "*Additional Info:*\nBuild terminated with state: FAILED"}]
            }, {
                "type": "section",
                "fields": [{"type": "mrkdwn", "text": "*Action:*\nTestAirbyteConnections"},
                    {"type": "mrkdwn", "text": "*Additional Info:*\nBuild terminated with state: FAILED"}]
            }, {"type": "section", "text": {"type": "mrkdwn", "text": "*Stage:* TEST"}}]
        }
        self._send_and_check_notification(event=event, expected_data=expected_data)

    def test_notification_handler_for_started_action(self) -> None:
        """
        Test notification handler for action started event
        """
        event = {
            'Records': [{
                'EventSource': 'aws:sns',
                'EventVersion': '1.0',
                'EventSubscriptionArn': 'arn:aws:sns:us-east-1:429533234373:airflow-infra-sandbox-manual-approval-topic:ced8975f-5757-4686-8515-176e858b4341',
                'Sns': {
                    'Type': 'Notification',
                    'MessageId': '3613389d-c56d-58cc-be3c-6314eba866dc',
                    'TopicArn': 'arn:aws:sns:us-east-1:429533234373:airflow-infra-sandbox-manual-approval-topic',
                    'Subject': None,
                    'Message': '{"account":"429533234373","detailType":"CodePipeline Action Execution State Change","region":"us-east-1","source":"aws.codepipeline","time":"2022-08-31T09:40:18Z","notificationRuleArn":"arn:aws:codestar-notifications:us-east-1:429533234373:notificationrule/aa57408d0e217613bb937c3f1f27f70b68478407","detail":{"pipeline":"mdp-pipeline-sandbox-pipeline","execution-id":"695b5c69-7afe-43c2-a5e7-778ad1763485","stage":"Approval","action":"ManualApproval","state":"STARTED","region":"us-east-1","type":{"owner":"AWS","provider":"Manual","category":"Approval","version":"1"},"version":5.0},"resources":["arn:aws:codepipeline:us-east-1:429533234373:mdp-pipeline-sandbox-pipeline"],"additionalAttributes":{"externalEntityLink":"","customData":"Please review the change set airbyte-changes-695b5c69-7afe-43c2-a5e7-778ad1763485 for the stack airbyte-sandbox-stack Please review the change set mdp-secrets-changes-695b5c69-7afe-43c2-a5e7-778ad1763485 for the stack mdp-secrets-sandbox-stack Please review the change set airflow-changes-695b5c69-7afe-43c2-a5e7-778ad1763485 for the stack airflow-sandbox-stack\\n"}}',
                    'Timestamp': '2022-08-31T09:40:21.200Z',
                    'SignatureVersion': '1',
                    'Signature': '38HttZBSIzkdD5vnCHCUkUm9mC6SOf63gp+yNrBSS4bnuyXwTci8oRkdt8Q6D/7yVe6ixlitGeLWzL/vjts475KwhIySddttdVcL+dW8m+4qFZLtj21AKUqtQemU29/5+vowEJMarRQ8VuEDFZu9fdX1LHq1Ih0cKAd9R9KgIkkF8P4D31E1svkkhVjB3oFQY4MQf9HQ0Ev7UzEdrEYt3xEiwqR5owaPrJd9Wp9k3tGEgEn47HRRF4o/YrGERrfrgIhggzygqYecp54NltlG2OCGEB/AKgb8DzFs3SN4/karycDYT9hxjyA1mBuBw8RE/8mIRG14fk7qsKDpgIw0Kw==',
                    'SigningCertUrl': 'https://sns.us-east-1.amazonaws.com/SimpleNotificationService-56e67fcb41f6fec09b0196692625d385.pem',
                    'UnsubscribeUrl': 'https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:429533234373:airflow-infra-sandbox-manual-approval-topic:ced8975f-5757-4686-8515-176e858b4341',
                    'MessageAttributes': {}
                }
            }]
        }
        self._send_and_check_notification(event=event, expected_data=None)
