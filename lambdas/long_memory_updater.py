"""
Lambda function for retrieving app role context based on user_id.

This module provides functionality to:
- Process incoming requests containing an user_id
- Validate the user_id input
- Retrieve corresponding app role content from DynamoDB
- Publish the results to a custom event bus

The module exposes:
- ContextRetriever: Main Lambda handler class for processing requests
- handler: Lambda entry point function

Environment Variables:
    APP_ROLE_TABLE_NAME: Name of the DynamoDB table containing app roles

Raises:
    ValueError: If user_id is missing or app role cannot be found
"""

import os
import sys

# Add `lambda/create/packages` to the system path.
# This must be done before importing any modules from the `packages` directory.
sys.path.append(os.path.join(os.path.dirname(__file__), "packages"))

from app_common.app_utils import http_request
from app_role_bo import AppRoleBO
from long_memory_bo import UserLongTermMemoryBO
from app_common.base_lambda_handler import BaseLambdaHandler


class LongMemoryUpdater(BaseLambdaHandler):
    """
    A Lambda handler for retrieving context based on the provided user_id.

    This class processes incoming events, validates inputs, retrieves app role content
    from the database, and publishes the results to a custom event bus.
    """

    def __gen_prompt_input_msg(
        self, current_summary: str, user_message: str, chatbot_response: str
    ):
        return f"""### Current Summary:
        {current_summary}
        
        ### New Message:
        User: {user_message}
        Chatbot: {chatbot_response}"""

    def __get_assistant_behaviour(self) -> str:
        return """You are an AI assistant responsible for maintaining a concise and accurate summary of a conversation.
        The summary should include only essential facts, unresolved issues, user preferences, or other important details that improve future interactions.

        ### Task:
        1. Determine if the new message is relevant to the current summary (e.g., it introduces new facts, updates existing details, or addresses unresolved issues).
        2. If the message is relevant, update the summary by incorporating the new information while keeping it as short as possible.
        3. If the message is not relevant, return the current summary unchanged.

        ### Output (in json format):
        {{"summary": "<updated summary>"}}
        """

    def _handle(self) -> dict:
        """
        Handle the incoming request, retrieve the app role, and publish the response.

        :return: A dictionary containing the app role and the original payload.
        :raises ValueError: If `user_id` is not provided or the app role cannot be found.
        """
        user_id = self.body.get("cbf_user_uuid", None)
        if not user_id:
            raise ValueError("cbf_user_uuid is required")

        user_msg = self.body.get("user_message", None)
        if not user_msg:
            raise ValueError("user_message is required")

        bot_msg = self.body.get("bot_message", None)
        if not bot_msg:
            raise ValueError("bot_message is required")

        # Retrieve the UserLongTermMemory table name from the environment variables.
        user_long_term_memory_table_name = self.get_env_var(
            "USER_LONG_TERM_MEMORY_TABLE_NAME"
        )
        user_long_term_memory_bo = UserLongTermMemoryBO(
            table_name=user_long_term_memory_table_name
        )

        last_memory_content = self.body.get("user_long_term_memory", None)

        # Prepare the AI job payload
        ai_job = {
            "category": "text-based",
            "input": {
                "text": self.__gen_prompt_input_msg(
                    current_summary=last_memory_content,
                    user_message=user_msg,
                    chatbot_response=bot_msg,
                ),
                "assistant_behaviour": self.__get_assistant_behaviour(),
            },
        }

        # ai_job["input"]["context"] = {
        #     "previous_messages": previous_messages,
        # }

        # Retrieve the AI job service URL from an SSM parameter
        ai_job_service_url = self.get_ssm_parameter_cached(
            self.get_env_var("AI_JOB_SERVICE_URL_SSM_FULL_PATH")
        )

        # Send the payload to the AI job service and get the response
        ai_job_result = http_request(
            url=ai_job_service_url, method="POST", json_data=ai_job
        )

        # Extract the chatbot-generated message from the response
        if "body" not in ai_job_result or ai_job_result["body"].get("output") is None:
            raise RuntimeError(f"Error while processing the message: {ai_job_result}")

        new_memory = ai_job_result["body"]["output"]

        last_memory_content = user_long_term_memory_bo.add_memory(
            user_id=user_id, memory=new_memory
        )

        self.do_log(f"New memory updated for the user {user_id}", new_memory)

        # nothing do return


def handler(event, context):
    """
    Lambda entry point for handling context retrieval requests.

    :param event: The event data passed to the Lambda function.
    :param context: The runtime information for the Lambda function.
    :return: The result from processing the event.
    """
    _handler = LongMemoryUpdater()
    # Implicitly invokes __call__(), which:
    #   - Executes _do_the_job(), which:
    #       - Calls before_handle(), handle(), and after_handle() methods.
    return _handler(event, context)
