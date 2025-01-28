"""
This module contains the business logic for the AppBehaviour entity.
"""

from functools import lru_cache
from app_common.dynamodb_utils import DynamoDBBase
from app_common.app_utils import http_request


class AppBehaviour:
    """
    Represents an AppBehaviour entity.
    """

    def __init__(self, app_id: str, behaviour_source: str) -> None:
        """
        Initializes an instance of the AppBehaviour class.

        :param app_id: Identifier for the application.
        :param behaviour_source: Source of the behaviour definition.
        """
        self.app_id = app_id
        self.behaviour_source = behaviour_source

    def to_dict(self) -> dict:
        """
        Generates a dictionary representation of the AppBehaviour entity.

        :return: Dictionary containing the AppBehaviour attributes.
        """
        return {
            "app_id": self.app_id,
            "behaviour_source": self.behaviour_source,
        }


class AppBehaviourBO(DynamoDBBase):
    """
    Business object for managing AppBehaviour entities.
    """

    def get_behaviour_content(self, app_id: str) -> str:
        """
        Retrieves the behaviour content for the specified application.

        :param app_id: Identifier for the application.
        :return: Content of the behaviour source as a string, or None if not found.
        """
        behaviour_source = self.get_behaviour_source(app_id)
        if not behaviour_source:
            return None

        if behaviour_source.startswith("http"):
            # The behaviour source is an HTTP URL, so we need to read its content.
            return self._load_url_content_as_text(behaviour_source)

        # else: return as is (Native behaviour Source)
        return behaviour_source

    @lru_cache(maxsize=128)
    def get_behaviour_source(self, app_id: str) -> str:
        """
        Retrieves the behaviour source URL for the specified application.

        :param app_id: Identifier for the application.
        :return: URL of the behaviour source, or None if not found.
        """
        response = self.get_by_partition_key(pk_name="app_id", pk_value=app_id)
        if not response:  # response is expected to be a list
            return None

        return response[0].get("behaviour_source")

    def _load_url_content_as_text(self, url: str) -> str:
        """
        Loads the content of the specified URL as text.

        :param url: URL to retrieve the content from.
        :return: Content of the URL as a string, or None if not found.
        """
        response = http_request("GET", url)
        return response.get("body")
