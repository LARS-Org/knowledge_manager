from aws_cdk import (
    Stack,
    aws_sns_subscriptions as sns_subscriptions,
)
from constructs import Construct

from app_common.app_common_stack import AppCommonStack


class KnowledgeManagerStack(AppCommonStack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the SNS topic "AddAIJobLastMessagesAttachedTopic"
        ai_job_last_msgs_topic = self._get_or_create_sns_topic(
            "AddAIJobLastMessagesAttachedTopic"
        )

        # Create the SNS topic "AIJobContextAttachedTopic"
        ai_job_context_attached_topic = self._get_or_create_sns_topic_with_sms_param(
            "AIJobContextAttachedTopic"
        )
