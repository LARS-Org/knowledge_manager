from aws_cdk import (
    aws_dynamodb as dynamodb,
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
            table_name="AppRoleTable",
            pk_name="app_id",
            pk_type=dynamodb.AttributeType.STRING,
            sk_name="source_type",
            sk_type=dynamodb.AttributeType.STRING,
        )

        # Create a lambda, using the method self._create_lambda, responsible for retrieve the AppRoles registers based on the app_id
        # The lambda will be named "AppRoleRetriever"
        self._create_lambda(
            name="AppRoleRetrieverLambda",
            handler="app_role_retriever.handler",
            environment={
                "APP_ROLE_TABLE_NAME": app_role_table.table_name,
            },
        )



        


