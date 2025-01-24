"""
Lambda function for updating a user's long-term memory using AI-generated summaries.

This function processes incoming events to retrieve user data, updates the user's
long-term memory with AI-generated content, and logs the process. It relies on
external services and utilities for AI processing, logging, and database interactions.
"""

import json
import os
import sys

# Add `lambda/create/packages` to the system path.
# This must be done before importing any modules from the `packages` directory.
sys.path.append(os.path.join(os.path.dirname(__file__), "packages"))

from app_common.app_utils import http_request
from long_memory_bo import UserLongTermMemoryBO
from app_common.base_lambda_handler import BaseLambdaHandler


class LongMemoryUpdater(BaseLambdaHandler):
    """
    A Lambda handler for updating the long-term memory of a user
    based on the interaction between a user and a chatbot.
    """

    def __gen_prompt_input_msg(
        self, current_summary: str, user_message: str, chatbot_response: str
    ) -> str:
        """
        Generate a prompt for the AI model based on the current summary,
        the user's message, and the chatbot's response.

        :param current_summary: The existing conversation summary.
        :param user_message: The latest message from the user.
        :param chatbot_response: The chatbot's response to the user's message.
        :return: A formatted string prompt for the AI model.
        """
        return f"""### Current Summary:
        {current_summary}
        
        ### New Message:
        User: {user_message}
        Chatbot: {chatbot_response}"""

    def __get_assistant_behaviour(self) -> str:
        """
        Provide the AI assistant's behavior instructions for updating the conversation summary.

        :return: A string detailing the assistant's behavior and task.
        """
        return """You are an AI assistant responsible for maintaining a concise and accurate summary of a conversation.
        The summary should include ONLY ESSENTIAL facts, unresolved issues, user preferences, user personal information, or other important details that improve future interactions.

        ### Task:
        1. Determine if the new message is relevant to the current summary (e.g., it introduces new facts, updates existing details, or addresses unresolved issues).
        2. If the message is relevant, update the summary by incorporating the new information while keeping it as short as possible.
        3. If the message is not relevant, return the current summary unchanged.

        ### Output (in json format):
        {{"summary": "<updated summary>"}}
        """

    def _handle(self) -> dict:
        """
        Handle the incoming request to update the user's long-term memory.

        :return: A dictionary containing the app role and the original payload.
        :raises ValueError: If required parameters are missing.
        """
        # Extract required data from the event body
        user_id = self.body.get("cbf_user_uuid")
        if not user_id:
            raise ValueError("cbf_user_uuid is required")

        user_msg = self.body.get("user_message")
        if not user_msg:
            raise ValueError("user_message is required")

        bot_msg = self.body.get("bot_message")
        if not bot_msg:
            raise ValueError("bot_message is required")

        # Retrieve the UserLongTermMemory table name from the environment variables
        user_long_term_memory_table_name = self.get_env_var(
            "USER_LONG_TERM_MEMORY_TABLE_NAME"
        )
        user_long_term_memory_bo = UserLongTermMemoryBO(
            table_name=user_long_term_memory_table_name
        )

        last_memory_content = self.body.get("user_long_term_memory")

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

        # Retrieve the AI job service URL from an SSM parameter
        ai_job_service_url = self.get_ssm_parameter_cached(
            self.get_env_var("AI_JOB_SERVICE_URL_SSM_FULL_PATH")
        )

        # Send the payload to the AI job service and get the response
        ai_job_result = http_request(
            url=ai_job_service_url, method="POST", json_data=ai_job
        )

        # Extract the AI-generated summary from the response
        if "body" not in ai_job_result or ai_job_result["body"].get("output") is None:
            raise RuntimeError(f"Error while processing the message: {ai_job_result}")

        ai_job_result = json.loads(ai_job_result["body"]["output"])

        self.do_log(ai_job_result, "AI Response")

        new_memory_content = ai_job_result["summary"]

        # Update the user's long-term memory in the database
        last_memory_content = user_long_term_memory_bo.add_memory(
            user_id=user_id, memory=new_memory_content
        )

        self.do_log(
            title=f"New memory updated for the user {user_id}", obj=new_memory_content
        )

        # No return value is required as the function completes its updates


def handler(event, context):
    """
    Lambda entry point for handling context retrieval requests.

    :param event: The event data passed to the Lambda function.
    :param context: The runtime information for the Lambda function.
    :return: The result from processing the event.
    """
    _handler = LongMemoryUpdater()
    # Invokes the BaseLambdaHandler logic chain
    return _handler(event, context)
