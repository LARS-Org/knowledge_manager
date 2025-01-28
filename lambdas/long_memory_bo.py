"""
This module contains the business logic for the UserLongTermMemory entity.
"""

from functools import lru_cache
import time

from app_common.dynamodb_utils import DynamoDBBase


class UserLongTermMemory:
    """
    Represents an UserLongTermMemory entity.
    """

    def __init__(self, user_id: str, memory: str) -> None:
        """
        Initializes an instance of the UserLongTermMemory class.

        :param user_id: Identifier for the user.
        :param memory: the user memory register.
        """
        self.user_id = user_id
        self.timestamp = int(time.time())
        self.memory = memory

    def to_dict(self) -> dict:
        """
        Generates a dictionary representation of the UserLongTermMemory entity.

        :return: Dictionary containing the UserLongTermMemory attributes.
        """
        return {
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "memory": self.memory,
        }


class UserLongTermMemoryBO(DynamoDBBase):
    """
    Business object for managing UserLongTermMemory entities.
    """

    @lru_cache
    def get_last_memory(self, user_id: str) -> UserLongTermMemory:
        """
        Retrieves the behaviour content for the specified application.

        :param user_id: Identifier for the application.
        :return: Memory as a UserLongTermMemory object, or None if not found.
        """
        response = self._get_last_items_by_key(
            key_name="user_id", key_value=user_id, k=1
        )
        if not response:  # response is expected to be a list
            return None
        # else: there is memory
        return response[0]

    def add_memory(self, user_id: str, memory: str) -> UserLongTermMemory:
        """
        Adds a new memory for the specified user.

        :param user_id: Identifier for the user.
        :param memory: the user memory register.
        """
        user_memory = UserLongTermMemory(user_id, memory)
        return self.add(user_memory)
