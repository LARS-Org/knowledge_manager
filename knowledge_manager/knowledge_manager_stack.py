"""
KnowledgeManagerStack manages knowledge-based AWS resources.

This stack creates and configures:
- DynamoDB table for storing app roles and their sources
- DynamoDB table for storing the user long-term memory
- Lambda function for retrieving context
- SNS topic for triggering context retrieval
- Subscription between SNS topic and Lambda

The DynamoDB table (AppRoleTable-v1) has:
- Partition key: app_id (STRING)
- Sort key: source_type
- Additional attribute: source

The DynamoDB table (UserLongTermMemoryTable) has:
- Partition Key: user_id (STRING)
- Sort key: timestamp (NUMBER)
- Additional attribute: memory

The Lambda function (ContextRetrieverLambda):
- Is triggered by SNS notifications
- Has access to read/write to the DynamoDB table
- Uses table name passed via environment variable

The SNS topic (KnowledgeManager-ContextToBeRetrieved):
- Triggers the context retriever Lambda function
- Manages notifications for context retrieval requests

Dependencies:
- aws_cdk.aws_dynamodb
- aws_cdk.aws_sns_subscriptions
- app_common.app_common_stack.AppCommonStack
"""

from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_sns_subscriptions as sns_subscriptions,
)
from constructs import Construct

from app_common.app_common_stack import AppCommonStack


class KnowledgeManagerStack(AppCommonStack):
    """
    A stack to manage knowledge-based resources, such as DynamoDB tables, SNS topics,
    and their associated Lambda functions.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """
        Initialize the KnowledgeManagerStack.

        :param scope: The scope in which this construct is defined.
        :param construct_id: The ID of this construct.
        :param kwargs: Additional parameters.
        """
        super().__init__(scope, construct_id, **kwargs)

        # This table includes an attribute "role_source" to persist
        # the source of the role itself.
        app_role_table = self._create_dynamodb_table(
            table_name="AppRoleTable-v1",
            pk_name="app_id",
            pk_type=dynamodb.AttributeType.STRING,
        )

        # This table includes an attribute named "memory" to persist
        # the user long-term memory version
        user_long_term_memory_table = self._create_dynamodb_table(
            table_name="UserLongTermMemoryTable",
            pk_name="user_id",
            pk_type=dynamodb.AttributeType.STRING,
            sk_name="timestamp",
            sk_type=dynamodb.AttributeType.NUMBER,  # Unix Epoch representation
        )

        # Lambda function for retrieving context, with an environment variable for the table name.
        context_retriever_lambda = self._create_lambda(
            name="ContextRetrieverLambda",
            handler="context_retriever.handler",
            environment={
                "APP_ROLE_TABLE_NAME": app_role_table.table_name,
                "USER_LONG_TERM_MEMORY_TABLE_NAME": user_long_term_memory_table.table_name,
            },
        )

        # Lambda function for updating the user long-term memory.
        user_long_term_memory_updater_lambda = self._create_lambda(
            name="UserLongTermMemoryUpdaterLambda",
            handler="long_memory_updater.handler",
            environment={
                "USER_LONG_TERM_MEMORY_TABLE_NAME": user_long_term_memory_table.table_name,
            },
        )

        # Grant the Lambda function full access to the DynamoDB tables.
        app_role_table.grant_full_access(context_retriever_lambda)
        user_long_term_memory_table.grant_read_data(context_retriever_lambda)
        user_long_term_memory_table.grant_full_access(
            user_long_term_memory_updater_lambda
        )

        # Create an SNS topic named "KnowledgeManager-ContextToBeRetrieved".
        context_tobe_retrieved_topic = self._create_sns_topic(
            topic_name="KnowledgeManager-ContextToBeRetrieved",
        )

        # Create an SNS topic named "KnowledgeManager-MemoryToBeUpdated"
        memory_tobe_updated_topic = self._create_sns_topic(
            topic_name="KnowledgeManager-MemoryToBeUpdated",
        )

        # Add a subscription to the topic to trigger the Lambda function.
        context_tobe_retrieved_topic.add_subscription(
            sns_subscriptions.LambdaSubscription(context_retriever_lambda)
        )

        memory_tobe_updated_topic.add_subscription(
            sns_subscriptions.LambdaSubscription(user_long_term_memory_updater_lambda)
        )

        # Define the SSM parameter for the AI Job Service URL
        ai_job_service_url_ssm_full_path = "/global/NewAIJobAPIURL"

        # Add the SSM parameter as an environment variable to the Lambda function
        user_long_term_memory_updater_lambda.add_environment(
            key="AI_JOB_SERVICE_URL_SSM_FULL_PATH",
            value=ai_job_service_url_ssm_full_path,
        )

        # Grant the Lambda function permission to read the SSM parameter
        self._grant_ssm_parameter_access(
            lambda_function=user_long_term_memory_updater_lambda,
            param_full_path=ai_job_service_url_ssm_full_path,
        )
