from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_sns_subscriptions as sns_subscriptions,
)
from constructs import Construct

from app_common.app_common_stack import AppCommonStack


class KnowledgeManagerStack(AppCommonStack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create a table using the self._create_dynamodb_table method
        # The table will be named "AppRoleTable"
        # the partition key will be the app_id
        # the sort key will be the source_type of the role ("txt_gdrive", "table" etc)
        # The table must have the attribute "source" to persist the source of the role itself
        app_role_table = self._create_dynamodb_table(
            table_name="AppRoleTable-v1",
            pk_name="app_id",
            pk_type=dynamodb.AttributeType.STRING,
        )

        # Create a lambda, using the method self._create_lambda, responsible
        # for retrieve the AppRole registered for the app_id
        # The lambda will be named "AppRoleRetriever"
        klg_retriever_lambda = self._create_lambda(
            name="KnowledgeRetrieverLambda",
            handler="knowledge_retriever.handler",
            environment={
                "APP_ROLE_TABLE_NAME": app_role_table.table_name,
            },
        )

        # Grant to lambda function full access to the table
        app_role_table.grant_full_access(klg_retriever_lambda)

        # Create SNS topic "KnowledgeManager-AppToHaveKLGRetrieved"
        app_to_have_klg_retrieved_topic = self._create_sns_topic(
            topic_name="KnowledgeManager-AppToHaveKLGRetrieved",
        )

        # Add a subscription to the topic to trigger the lambda function
        app_to_have_klg_retrieved_topic.add_subscription(
            sns_subscriptions.LambdaSubscription(klg_retriever_lambda)
        )
