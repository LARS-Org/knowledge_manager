import os
import sys

# Adds lambda/create/packages to the system path.
# This must be done before importing any modules from the packages directory.
sys.path.append(os.path.join(os.path.dirname(__file__), "packages"))

from lambdas.app_role_bo import AppRoleBO
from app_common.base_lambda_handler import BaseLambdaHandler


class KnowledgeRetriever(BaseLambdaHandler):
    """
    This class is responsible for
    """

    def _handle(self) -> dict:
        """ """
        app_id = self.body.get("app_id", None)

        if not app_id:
            raise ValueError("app_id is required")

        # else: app_id is present

        app_role_table_name = self.get_env_var("APP_ROLE_TABLE_NAME")
        app_role_bo = AppRoleBO(table_name=app_role_table_name)

        app_role = app_role_bo.get_role_content(app_id=app_id)

        if not app_role:
            raise ValueError(f"AppRole not found for app_id: {app_id}")

        payload = self.body | {"app_role": app_role}

        # Publish the response to the event bus
        self.publish_to_custom_event_bus(
            message=payload,
            detail_type="KnowledgeRetrieved",
        )

        return payload


def handler(event, context):
    """
    Lambda function to 
    """
    _handler = KnowledgeRetriever()
    # Implicitly invokes __call__() ...
    #   ... which invokes _do_the_job() ...
    #     ... which invokes before_handle(), handle() and after_handle()
    return _handler(event, context)
