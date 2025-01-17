"""
This module contains the business logic for the AppRole entity.
"""

from functools import lru_cache
from app_common.dynamodb_utils import DynamoDBBase
from app_common.app_utils import http_request


class AppRole:
    """
    Represents an AppRole entity.
    """

    def __init__(self, app_id: str, role_source: str) -> None:
        """
        Initializes an instance of the AppRole class.

        :param app_id: Identifier for the application.
        :param role_source: Source of the role definition.
        """
        self.app_id = app_id
        self.role_source = role_source

    def to_dict(self) -> dict:
        """
        Generates a dictionary representation of the AppRole entity.

        :return: Dictionary containing the AppRole attributes.
        """
        return {
            "app_id": self.app_id,
            "role_source": self.role_source,
        }


class AppRoleBO(DynamoDBBase):
    """
    Business object for managing AppRole entities.
    """

    def get_role_content(self, app_id: str) -> str:
        """
        Retrieves the role content for the specified application.

        :param app_id: Identifier for the application.
        :return: Content of the role source as a string, or None if not found.
        """
        role_source = self.get_role_source(app_id)
        if not role_source:
            return None

        if role_source.startswith("http"):
            # The role source is an HTTP URL, so we need to read its content.
            return self._load_url_content_as_text(role_source)

        # else: return as is (Native Role Source)
        return role_source

    @lru_cache(maxsize=128)
    def get_role_source(self, app_id: str) -> str:
        """
        Retrieves the role source URL for the specified application.

        :param app_id: Identifier for the application.
        :return: URL of the role source, or None if not found.
        """
        response = self.get_by_partition_key(pk_name="app_id", pk_value=app_id)
        if not response:  # response is expected to be a list
            return None

        return response[0].get("role_source")

    def _load_url_content_as_text(self, url: str) -> str:
        """
        Loads the content of the specified URL as text.

        :param url: URL to retrieve the content from.
        :return: Content of the URL as a string, or None if not found.
        """
        response = http_request("GET", url)
        return response.get("body")
