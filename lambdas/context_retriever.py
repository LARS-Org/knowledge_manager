"""
Lambda function for retrieving app role context based on app_id.

This module provides functionality to:
- Process incoming requests containing an app_id
- Validate the app_id input
- Retrieve corresponding app role content from DynamoDB
- Publish the results to a custom event bus

The module exposes:
- ContextRetriever: Main Lambda handler class for processing requests
- handler: Lambda entry point function

Environment Variables:
    APP_ROLE_TABLE_NAME: Name of the DynamoDB table containing app roles

Raises:
    ValueError: If app_id is missing or app role cannot be found
"""

import os
import sys

# Add `lambda/create/packages` to the system path.
# This must be done before importing any modules from the `packages` directory.
sys.path.append(os.path.join(os.path.dirname(__file__), "packages"))

from app_role_bo import AppRoleBO
from long_memory_bo import UserLongTermMemoryBO
from app_common.base_lambda_handler import BaseLambdaHandler


class ContextRetriever(BaseLambdaHandler):
    """
    A Lambda handler for retrieving context based on the provided app_id.

    This class processes incoming events, validates inputs, retrieves app role content
    from the database, and publishes the results to a custom event bus.
    """

    def _handle(self) -> dict:
        """
        Handle the incoming request, retrieve the app role, and publish the response.

        :return: A dictionary containing the app role and the original payload.
        :raises ValueError: If `app_id` is not provided or the app role cannot be found.
        """
        app_id = self.body.get("app_id")

        if not app_id:
            raise ValueError("app_id is required")

        # Retrieve the AppRole table name from the environment variables.
        app_role_table_name = self.get_env_var("APP_ROLE_TABLE_NAME")
        app_role_bo = AppRoleBO(table_name=app_role_table_name)

        # Fetch the app role content using the app_id.
        app_role = app_role_bo.get_role_content(app_id=app_id)

        if not app_role:
            raise ValueError(f"AppRole not found for app_id: {app_id}")

        # Retrieve the UserLongTermMemory table name from the environment variables.
        user_long_term_memory_table_name = self.get_env_var(
            "USER_LONG_TERM_MEMORY_TABLE_NAME"
        )
        user_long_term_memory_bo = UserLongTermMemoryBO(
            table_name=user_long_term_memory_table_name
        )

        # Fetch the user long-term memory content using the user_id
        user_id = self.body.get("cbf_user_uuid")

        if not user_id:
            raise ValueError("user_id is required")

        user_long_term_memory = user_long_term_memory_bo.get_last_memory(
            user_id=user_id
        )

        last_memory_content = None

        if user_long_term_memory:
            last_memory_content = user_long_term_memory["memory"]

        # Include the retrieved app role in the response payload.
        payload = {
            **self.body,
            "app_role": app_role,
            "user_long_term_memory": last_memory_content,
        }

        # Publish the response to the custom event bus.
        self.publish_to_custom_event_bus(
            message=payload,
            detail_type="ContextRetrieved",
        )

        return payload


def handler(event, context):
    """
    Lambda entry point for handling context retrieval requests.

    :param event: The event data passed to the Lambda function.
    :param context: The runtime information for the Lambda function.
    :return: The result from processing the event.
    """
    _handler = ContextRetriever()
    # Implicitly invokes __call__(), which:
    #   - Executes _do_the_job(), which:
    #       - Calls before_handle(), handle(), and after_handle() methods.
    return _handler(event, context)
